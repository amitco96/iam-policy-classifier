"""
FastAPI application entry point for IAM Policy Classifier.

Initializes the app with:
- Metadata (title, version, contact, license)
- CORS middleware
- Request logging + request-ID tracking middleware
- Consistent JSON error handlers (404, 500, validation)
- Lifespan events for startup/shutdown logging
- GET /health endpoint
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.middleware.logging import RequestLoggingMiddleware
from src.api.routes.classify import limiter, router as classify_router
from src.api.routes.history import router as history_router
from src.config import settings, validate_settings
from src.models.schemas import ErrorDetail, ErrorResponse, HealthResponse
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)


# ============================================================================
# Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Handle startup and shutdown events."""
    # --- Startup ---
    setup_logging()
    logger.info(
        "Starting application",
        extra={"app": settings.APP_NAME, "version": settings.APP_VERSION},
    )
    validate_settings()

    yield

    # --- Shutdown ---
    logger.info(
        "Shutting down application gracefully",
        extra={"app": settings.APP_NAME},
    )


# ============================================================================
# App Initialization
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready IAM policy security classification API",
    version=settings.APP_VERSION,
    contact={
        "name": "IAM Policy Classifier",
        "url": "https://github.com/amitco96/iam-policy-classifier",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)

# Attach the slowapi limiter so it can track request counts.
app.state.limiter = limiter

# CORS — must be added before the logging middleware so preflight requests
# are handled without generating spurious 500 log entries.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOWED_METHODS,
    allow_headers=settings.CORS_ALLOWED_HEADERS,
)

app.add_middleware(RequestLoggingMiddleware)


# ============================================================================
# Helper
# ============================================================================

def _json_error(
    code: str,
    message: str,
    http_status: int,
    details: str | None = None,
) -> JSONResponse:
    """Build a consistently-shaped JSON error response."""
    body = ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details)
    )
    return JSONResponse(
        status_code=http_status,
        content=body.model_dump(exclude_none=True),
    )


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return _json_error(
            code="NOT_FOUND",
            message=f"Resource not found: {request.url.path}",
            http_status=status.HTTP_404_NOT_FOUND,
        )
    return _json_error(
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        http_status=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _json_error(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=str(exc.errors()),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.error("Unhandled exception", exc_info=exc)
    return _json_error(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        # Expose detail in non-production environments only.
        details=str(exc) if not settings.is_production() else None,
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    return _json_error(
        code="RATE_LIMIT_EXCEEDED",
        message=f"Rate limit exceeded: {exc.detail}",
        http_status=status.HTTP_429_TOO_MANY_REQUESTS,
    )


# ============================================================================
# Routes
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the current health status and runtime configuration of the application.",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """Lightweight liveness probe — no external dependencies queried."""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
        available_providers=settings.get_available_providers(),
    )


app.include_router(classify_router)
app.include_router(history_router)
