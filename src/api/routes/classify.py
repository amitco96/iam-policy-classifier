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
