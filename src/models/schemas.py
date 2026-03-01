"""
Pydantic schemas for request/response models.

These models are used for API input validation, serialization, and
OpenAPI documentation generation.
"""

from typing import List, Optional
from pydantic import BaseModel


# ============================================================================
# Health Check
# ============================================================================

class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""

    status: str
    version: str
    environment: str
    timestamp: str
    available_providers: List[str]

    model_config = {"json_schema_extra": {"example": {
        "status": "healthy",
        "version": "0.1.0",
        "environment": "development",
        "timestamp": "2026-03-01T12:00:00+00:00",
        "available_providers": ["claude"],
    }}}


# ============================================================================
# Error Responses
# ============================================================================

class ErrorDetail(BaseModel):
    """Structured error detail embedded in every error response."""

    code: str
    message: str
    details: Optional[str] = None


class ErrorResponse(BaseModel):
    """Consistent error envelope returned by all exception handlers."""

    error: ErrorDetail

    model_config = {"json_schema_extra": {"example": {
        "error": {
            "code": "NOT_FOUND",
            "message": "The requested resource was not found",
            "details": None,
        }
    }}}
