"""
Classification endpoint — POST /classify.

Accepts an IAM policy document, validates its structure via the PolicyInput
Pydantic model, delegates to ClassificationService, and returns a
ClassificationResult with category, risk score, and recommendations.

Rate limiting: 10 requests per minute per client IP (via slowapi).
Error mapping:
    400 — structural validation of the policy JSON (raised explicitly below)
    422 — Pydantic schema validation failures (handled by FastAPI automatically)
    429 — rate limit exceeded (handled by the RateLimitExceeded exception handler)
    500 — unexpected LLM API error
    503 — LLM provider not configured or connection failure
"""

import asyncio
import json
import logging
import time

import anthropic
import openai
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings
from src.core.classifier import ClassificationService
from src.models.schemas import (
    BatchClassificationResult,
    BatchPolicyInput,
    ClassificationCategory,
    ClassificationResult,
    ErrorDetail,
    ErrorResponse,
    PolicyInput,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter — exported so main.py can attach it to app.state and register
# the RateLimitExceeded exception handler.
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Classifier singleton — async LLM clients are initialised in __init__ only
# when the corresponding API keys are present in settings.
# ---------------------------------------------------------------------------
_classifier = ClassificationService()

# ---------------------------------------------------------------------------
# Severity ordering used to determine highest_risk_category in batch results.
# ---------------------------------------------------------------------------
_SEVERITY: dict[ClassificationCategory, int] = {
    ClassificationCategory.compliant: 0,
    ClassificationCategory.needs_review: 1,
    ClassificationCategory.overly_permissive: 2,
    ClassificationCategory.insecure: 3,
}

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(tags=["Classification"])


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _error_json(
    code: str,
    message: str,
    http_status: int,
    details: str | None = None,
) -> JSONResponse:
    """Return a consistently-shaped JSON error response (matches the envelope
    used by the global exception handlers in main.py)."""
    body = ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details)
    )
    return JSONResponse(
        status_code=http_status,
        content=body.model_dump(exclude_none=True),
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/classify",
    response_model=ClassificationResult,
    summary="Classify IAM Policy",
    description=(
        "Analyse an AWS IAM policy document for security risks. "
        "Returns a classification category (compliant / needs_review / "
        "overly_permissive / insecure), a numeric risk score (0–100), "
        "a human-readable explanation, and prioritised remediation "
        "recommendations."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Invalid IAM policy structure",
            "content": {"application/json": {"example": {
                "error": {
                    "code": "INVALID_POLICY",
                    "message": "policy_json is missing required IAM policy keys: ['Version']",
                }
            }}},
        },
        422: {"description": "Request body failed schema validation"},
        429: {
            "description": "Rate limit exceeded (max 10 requests / minute per IP)",
            "content": {"application/json": {"example": {
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded: 10 per 1 minute",
                }
            }}},
        },
        500: {
            "description": "LLM provider returned an unexpected error",
            "content": {"application/json": {"example": {
                "error": {"code": "LLM_API_ERROR", "message": "LLM provider returned an unexpected error."}
            }}},
        },
        503: {
            "description": "LLM provider unavailable or not configured",
            "content": {"application/json": {"example": {
                "error": {"code": "SERVICE_UNAVAILABLE", "message": "Classification service is temporarily unreachable."}
            }}},
        },
    },
)
@limiter.limit(f"{settings.API_RATE_LIMIT}/minute")
async def classify_policy(
    request: Request,
    body: PolicyInput,
) -> ClassificationResult | JSONResponse:
    """
    Classify a single IAM policy document for security risks.

    The provider field defaults to the application's DEFAULT_LLM_PROVIDER
    setting when omitted. Pydantic validates both the provider name and the
    presence of 'Version'/'Statement' keys before this handler is called.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    provider = body.provider or settings.DEFAULT_LLM_PROVIDER

    # Log the incoming request with sizing context.
    policy_bytes = len(json.dumps(body.policy_json))
    statement_count = len(body.policy_json.get("Statement", []))

    logger.info(
        "Classification request received",
        extra={
            "request_id": request_id,
            "provider": provider,
            "policy_size_bytes": policy_bytes,
            "statement_count": statement_count,
        },
    )

    start_time = time.perf_counter()

    try:
        result = await _classifier.classify_policy(body.policy_json, provider)

    except ValueError as exc:
        # Raised when the requested provider is not configured or unsupported.
        logger.warning(
            "Provider unavailable: %s",
            exc,
            extra={"request_id": request_id, "provider": provider},
        )
        return _error_json(
            code="SERVICE_UNAVAILABLE",
            message=str(exc),
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except (anthropic.APIConnectionError, openai.APIConnectionError) as exc:
        logger.error(
            "LLM connection failed",
            extra={
                "request_id": request_id,
                "provider": provider,
                "error": str(exc),
            },
        )
        return _error_json(
            code="SERVICE_UNAVAILABLE",
            message="Classification service is temporarily unreachable. Please retry.",
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except (anthropic.RateLimitError, openai.RateLimitError) as exc:
        logger.error(
            "LLM upstream rate limit reached",
            extra={
                "request_id": request_id,
                "provider": provider,
                "error": str(exc),
            },
        )
        return _error_json(
            code="SERVICE_UNAVAILABLE",
            message="LLM provider rate limit reached. Please retry in a moment.",
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except (anthropic.APIStatusError, openai.APIStatusError) as exc:
        logger.error(
            "LLM API status error",
            extra={
                "request_id": request_id,
                "provider": provider,
                "llm_status_code": exc.status_code,
                "error": str(exc),
            },
        )
        return _error_json(
            code="LLM_API_ERROR",
            message="LLM provider returned an unexpected error.",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=str(exc) if not settings.is_production() else None,
        )

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Unexpected error during classification",
            exc_info=exc,
            extra={"request_id": request_id, "provider": provider},
        )
        return _error_json(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred during classification.",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=str(exc) if not settings.is_production() else None,
        )

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    logger.info(
        "Classification completed",
        extra={
            "request_id": request_id,
            "provider": provider,
            "category": result.category.value,
            "risk_score": result.risk_score,
            "confidence": result.confidence,
            "duration_ms": duration_ms,
        },
    )

    return result


# ---------------------------------------------------------------------------
# Batch — internal helper
# ---------------------------------------------------------------------------

async def _classify_single(
    index: int,
    policy_input: PolicyInput,
    request_id: str,
) -> tuple[int, ClassificationResult | BaseException]:
    """Classify one policy and always return (index, result_or_exception).

    Never raises; exceptions are captured and returned so that
    asyncio.gather can continue processing the rest of the batch.
    """
    provider = policy_input.provider or settings.DEFAULT_LLM_PROVIDER
    try:
        result = await _classifier.classify_policy(policy_input.policy_json, provider)
        return index, result
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Individual policy classification failed at index %d: %s",
            index,
            exc,
            extra={
                "request_id": request_id,
                "policy_index": index,
                "error": str(exc),
            },
        )
        return index, exc


# ---------------------------------------------------------------------------
# Batch endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/classify/batch",
    response_model=BatchClassificationResult,
    summary="Batch Classify IAM Policies",
    description=(
        "Analyse up to 10 AWS IAM policy documents concurrently for security "
        "risks. All policies are dispatched simultaneously via asyncio.gather. "
        "Partial failures are tolerated — successfully classified policies are "
        "always returned. Returns 500 only when every policy in the batch fails."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        422: {
            "description": (
                "Request body failed schema validation "
                "(e.g. empty list or more than 10 policies)"
            ),
        },
        429: {
            "description": "Rate limit exceeded (max 5 requests / minute per IP)",
            "content": {"application/json": {"example": {
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded: 5 per 1 minute",
                }
            }}},
        },
        500: {
            "description": "Every policy in the batch failed to classify",
            "content": {"application/json": {"example": {
                "error": {
                    "code": "ALL_CLASSIFICATIONS_FAILED",
                    "message": "Every policy in the batch failed to classify.",
                }
            }}},
        },
    },
)
@limiter.limit("5/minute")
async def classify_batch(
    request: Request,
    body: BatchPolicyInput,
) -> BatchClassificationResult | JSONResponse:
    """
    Classify multiple IAM policy documents concurrently.

    Policies are dispatched in parallel; individual failures are logged with
    their zero-based index and do not abort the remaining classifications.
    Returns 500 only when every policy fails.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    total_policies = len(body.policies)

    logger.info(
        "Batch classification request received",
        extra={"request_id": request_id, "batch_size": total_policies},
    )

    start_time = time.perf_counter()

    # Dispatch all classifications concurrently.
    outcomes: list[tuple[int, ClassificationResult | BaseException]] = (
        await asyncio.gather(
            *[_classify_single(i, p, request_id) for i, p in enumerate(body.policies)]
        )
    )

    # Partition into successes and failures.
    results: list[ClassificationResult] = []
    failed = 0
    for _idx, outcome in outcomes:
        if isinstance(outcome, BaseException):
            failed += 1
        else:
            results.append(outcome)

    successful = len(results)

    if successful == 0:
        logger.error(
            "Batch classification: all %d policies failed",
            total_policies,
            extra={"request_id": request_id, "total_policies": total_policies, "failed": failed},
        )
        return _error_json(
            code="ALL_CLASSIFICATIONS_FAILED",
            message="Every policy in the batch failed to classify.",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    average_risk_score = round(sum(r.risk_score for r in results) / successful, 2)
    highest_risk_category = max(results, key=lambda r: _SEVERITY[r.category]).category

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    logger.info(
        "Batch classification completed",
        extra={
            "request_id": request_id,
            "total_policies": total_policies,
            "successful": successful,
            "failed": failed,
            "average_risk_score": average_risk_score,
            "highest_risk_category": highest_risk_category.value,
            "duration_ms": duration_ms,
        },
    )

    return BatchClassificationResult(
        results=results,
        total_policies=total_policies,
        successful=successful,
        failed=failed,
        average_risk_score=average_risk_score,
        highest_risk_category=highest_risk_category,
    )
