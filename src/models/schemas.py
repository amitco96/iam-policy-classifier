"""
Pydantic schemas for request/response models.

These models are used for API input validation, serialization, and
OpenAPI documentation generation.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


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


# ============================================================================
# Classification — Inputs
# ============================================================================

class PolicyInput(BaseModel):
    """
    Request body for a single IAM policy classification.

    Validates that the supplied JSON document is a plausible IAM policy
    (contains 'Version' and 'Statement' keys) and that the requested LLM
    provider is currently configured in the application settings.
    """

    policy_json: Dict = Field(
        description="The IAM policy document to analyse.",
        examples=[{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "s3:*",
                    "Resource": "*",
                }
            ],
        }],
    )
    provider: Optional[str] = Field(
        default="claude",
        description="LLM provider to use for classification ('claude' or 'openai').",
        examples=["claude"],
    )

    @field_validator("policy_json")
    @classmethod
    def validate_policy_structure(cls, v: Dict) -> Dict:
        """Reject documents that are missing the top-level IAM policy keys."""
        missing = [key for key in ("Version", "Statement") if key not in v]
        if missing:
            raise ValueError(
                f"policy_json is missing required IAM policy keys: {missing}"
            )
        if not isinstance(v["Statement"], list):
            raise ValueError("policy_json['Statement'] must be a list")
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Ensure the requested provider has an API key configured at runtime."""
        # Import here to avoid a circular dependency at module load time and to
        # allow tests to patch settings without import-order issues.
        from src.config import settings

        available = settings.get_available_providers()
        if v not in available:
            raise ValueError(
                f"Provider '{v}' is not available. "
                f"Configured providers: {available}"
            )
        return v


# ============================================================================
# Classification — Category Enum
# ============================================================================

class ClassificationCategory(str, Enum):
    """
    Enumeration of possible IAM policy security classifications.

    Inheriting from str allows the value to serialise directly to a JSON
    string without extra transformation.
    """

    compliant = "compliant"
    needs_review = "needs_review"
    overly_permissive = "overly_permissive"
    insecure = "insecure"


# ============================================================================
# Classification — Result
# ============================================================================

class ClassificationResult(BaseModel):
    """
    The full output produced by the classification engine for a single policy.

    Includes the security category, a numeric risk score, human-readable
    explanation, and a prioritised list of remediation recommendations.
    """

    category: ClassificationCategory = Field(
        description="Security classification assigned to the policy.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Model confidence in the classification (0.0 – 1.0).",
    )
    risk_score: int = Field(
        ge=0,
        le=100,
        description="Numeric risk score where 0 = no risk and 100 = critical.",
    )
    explanation: str = Field(
        description="Human-readable explanation of why this classification was assigned.",
    )
    recommendations: List[str] = Field(
        description="Ordered list of actionable security improvements.",
    )
    provider_used: str = Field(
        description="LLM provider that produced this result.",
    )
    analyzed_at: datetime = Field(
        description="UTC timestamp of when the analysis was performed.",
    )
    policy_summary: Optional[str] = Field(
        default=None,
        description="Brief description of what the policy actually permits.",
    )

    model_config = {"json_schema_extra": {"example": {
        "category": "overly_permissive",
        "confidence": 0.92,
        "risk_score": 75,
        "explanation": (
            "Policy grants s3:* to all resources (*), violating the principle "
            "of least privilege and exposing every S3 bucket in the account."
        ),
        "recommendations": [
            "Replace 's3:*' with the minimum required actions (e.g. s3:GetObject).",
            "Restrict the Resource ARN to specific bucket(s) rather than '*'.",
            "Consider adding a Condition block to limit access by IP or VPC.",
        ],
        "provider_used": "claude",
        "analyzed_at": "2026-03-01T12:00:00+00:00",
        "policy_summary": "Grants full S3 access to all resources.",
    }}}


# ============================================================================
# Batch — Inputs
# ============================================================================

class BatchPolicyInput(BaseModel):
    """
    Request body for classifying multiple IAM policies in a single call.

    Between 1 and 10 policies may be submitted per request. Each policy
    is validated independently using the same rules as PolicyInput.
    """

    policies: List[PolicyInput] = Field(
        min_length=1,
        max_length=10,
        description="List of IAM policies to classify (1 – 10 items).",
        examples=[[{
            "policy_json": {
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"}],
            },
            "provider": "claude",
        }]],
    )


# ============================================================================
# Batch — Result
# ============================================================================

class BatchClassificationResult(BaseModel):
    """
    Aggregate response returned after batch classification.

    Includes only the successfully-classified per-policy results together
    with summary statistics: total submitted, success/failure counts,
    average risk score, and the highest-severity category found.
    """

    results: List[ClassificationResult] = Field(
        description="Classification results for each successfully classified policy.",
    )
    total_policies: int = Field(
        description="Total number of policies submitted in the batch.",
    )
    successful: int = Field(
        description="Number of policies that were successfully classified.",
    )
    failed: int = Field(
        description="Number of policies that failed to classify.",
    )
    average_risk_score: float = Field(
        description="Mean risk score across all successfully classified policies.",
    )
    highest_risk_category: ClassificationCategory = Field(
        description="Most severe classification category found among successful results.",
    )

    model_config = {"json_schema_extra": {"example": {
        "results": [],
        "total_policies": 3,
        "successful": 3,
        "failed": 0,
        "average_risk_score": 48.3,
        "highest_risk_category": "overly_permissive",
    }}}
