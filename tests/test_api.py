"""
API integration tests for IAM Policy Classifier.

Exercises the full HTTP stack — middleware, Pydantic validation, exception
handlers, response serialisation — using FastAPI's TestClient.
All LLM calls are mocked via the module-level _classifier singleton in
src.api.routes.classify; no real API keys or network access required.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from src.api.main import app
from src.models.schemas import ClassificationCategory, ClassificationResult


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_result(
    category: str = "compliant",
    risk_score: int = 10,
    provider: str = "claude",
) -> ClassificationResult:
    """Return a minimal but fully-populated ClassificationResult."""
    return ClassificationResult(
        category=ClassificationCategory(category),
        confidence=0.9,
        risk_score=risk_score,
        explanation="Policy follows least-privilege principles.",
        recommendations=["No changes required."],
        provider_used=provider,
        analyzed_at=datetime.now(timezone.utc),
        policy_summary="Grants limited read-only access.",
    )


def _policy_body() -> dict:
    """Valid single-classify request body."""
    return {
        "policy_json": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject"],
                    "Resource": "arn:aws:s3:::my-bucket/*",
                }
            ],
        },
        "provider": "claude",
    }


def _batch_body(n: int) -> dict:
    """Valid batch request body containing n identical policies."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject"],
                "Resource": "arn:aws:s3:::my-bucket/*",
            }
        ],
    }
    return {
        "policies": [
            {"policy_json": policy, "provider": "claude"}
            for _ in range(n)
        ]
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """
    TestClient for the FastAPI app.
    Lifespan (startup/shutdown) runs exactly once for the module.
    raise_server_exceptions=False: tests receive HTTP responses even if
    an exception slips past all handlers.
    """
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def mock_classifier():
    """
    Patch the module-level _classifier singleton for the duration of one test.
    classify_policy is replaced with an AsyncMock so tests can set
    return_value or side_effect without touching real LLM clients.
    """
    with patch("src.api.routes.classify._classifier") as mock_svc:
        mock_svc.classify_policy = AsyncMock()
        yield mock_svc


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """
    Clear the in-memory rate limit counters before every test so that
    tests don't consume each other's quota (e.g. the 5/min batch limit).
    """
    from src.api.routes.classify import limiter
    limiter._storage.reset()
    yield


# ---------------------------------------------------------------------------
# a) GET /health
# ---------------------------------------------------------------------------

def test_health_returns_200(client):
    assert client.get("/health").status_code == 200


def test_health_status_is_healthy(client):
    assert client.get("/health").json()["status"] == "healthy"


def test_health_response_has_required_fields(client):
    data = client.get("/health").json()
    for field in ("status", "version", "environment", "timestamp", "available_providers"):
        assert field in data, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# b) POST /classify — valid policy → 200 + ClassificationResult shape
# ---------------------------------------------------------------------------

def test_classify_valid_policy_returns_200(client, mock_classifier):
    mock_classifier.classify_policy.return_value = _make_result()
    assert client.post("/classify", json=_policy_body()).status_code == 200


def test_classify_response_has_all_result_fields(client, mock_classifier):
    mock_classifier.classify_policy.return_value = _make_result("insecure", risk_score=90)
    data = client.post("/classify", json=_policy_body()).json()
    for field in (
        "category", "confidence", "risk_score",
        "explanation", "recommendations", "provider_used", "analyzed_at",
    ):
        assert field in data, f"Missing field in ClassificationResult: {field}"


def test_classify_response_values_reflect_mock(client, mock_classifier):
    mock_classifier.classify_policy.return_value = _make_result("insecure", risk_score=90)
    data = client.post("/classify", json=_policy_body()).json()
    assert data["category"] == "insecure"
    assert data["risk_score"] == 90
    assert data["provider_used"] == "claude"


# ---------------------------------------------------------------------------
# c) POST /classify — missing policy_json → 422
# ---------------------------------------------------------------------------

def test_classify_missing_policy_json_returns_422(client):
    response = client.post("/classify", json={"provider": "claude"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# d) POST /classify — policy_json is not a dict → 422
# ---------------------------------------------------------------------------

def test_classify_policy_json_string_returns_422(client):
    response = client.post("/classify", json={"policy_json": "not-a-dict", "provider": "claude"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_classify_policy_json_list_returns_422(client):
    response = client.post("/classify", json={"policy_json": [1, 2, 3], "provider": "claude"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# e) POST /classify — 503 when no API keys configured / provider unavailable
# ---------------------------------------------------------------------------

def test_classify_returns_503_on_provider_value_error(client, mock_classifier):
    mock_classifier.classify_policy.side_effect = ValueError(
        "Anthropic client is not available — ANTHROPIC_API_KEY is not configured."
    )
    response = client.post("/classify", json=_policy_body())
    assert response.status_code == 503


def test_classify_503_error_code_is_service_unavailable(client, mock_classifier):
    mock_classifier.classify_policy.side_effect = ValueError("provider not configured")
    data = client.post("/classify", json=_policy_body()).json()
    assert data["error"]["code"] == "SERVICE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# f) POST /classify — 500 when ClassificationService raises unexpected exception
# ---------------------------------------------------------------------------

def test_classify_returns_500_on_unexpected_exception(client, mock_classifier):
    mock_classifier.classify_policy.side_effect = RuntimeError("disk on fire")
    response = client.post("/classify", json=_policy_body())
    assert response.status_code == 500


def test_classify_500_error_code_is_internal_server_error(client, mock_classifier):
    mock_classifier.classify_policy.side_effect = RuntimeError("disk on fire")
    data = client.post("/classify", json=_policy_body()).json()
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"


# ---------------------------------------------------------------------------
# g) POST /classify/batch — valid batch of 2 → 200, total=2, successful=2, failed=0
# ---------------------------------------------------------------------------

def test_batch_two_policies_returns_200(client, mock_classifier):
    mock_classifier.classify_policy.return_value = _make_result()
    assert client.post("/classify/batch", json=_batch_body(2)).status_code == 200


def test_batch_two_policies_counts(client, mock_classifier):
    mock_classifier.classify_policy.return_value = _make_result()
    data = client.post("/classify/batch", json=_batch_body(2)).json()
    assert data["total_policies"] == 2
    assert data["successful"] == 2
    assert data["failed"] == 0
    assert len(data["results"]) == 2


def test_batch_response_has_required_fields(client, mock_classifier):
    mock_classifier.classify_policy.return_value = _make_result()
    data = client.post("/classify/batch", json=_batch_body(1)).json()
    for field in (
        "results", "total_policies", "successful",
        "failed", "average_risk_score", "highest_risk_category",
    ):
        assert field in data, f"Missing field in BatchClassificationResult: {field}"


# ---------------------------------------------------------------------------
# h) POST /classify/batch — empty list → 422
# ---------------------------------------------------------------------------

def test_batch_empty_list_returns_422(client):
    response = client.post("/classify/batch", json={"policies": []})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# i) POST /classify/batch — 11 policies (over max of 10) → 422
# ---------------------------------------------------------------------------

def test_batch_eleven_policies_returns_422(client):
    response = client.post("/classify/batch", json=_batch_body(11))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# j) POST /classify/batch — 1 of 2 fails → 200, successful=1, failed=1
# ---------------------------------------------------------------------------

def test_batch_partial_failure_returns_200(client, mock_classifier):
    mock_classifier.classify_policy.side_effect = [
        _make_result("compliant", risk_score=10),
        RuntimeError("LLM timeout on policy 2"),
    ]
    assert client.post("/classify/batch", json=_batch_body(2)).status_code == 200


def test_batch_partial_failure_counts(client, mock_classifier):
    mock_classifier.classify_policy.side_effect = [
        _make_result("compliant", risk_score=10),
        RuntimeError("LLM timeout on policy 2"),
    ]
    data = client.post("/classify/batch", json=_batch_body(2)).json()
    assert data["total_policies"] == 2
    assert data["successful"] == 1
    assert data["failed"] == 1
    assert len(data["results"]) == 1


# ---------------------------------------------------------------------------
# k) POST /classify/batch — all fail → 500, code=ALL_CLASSIFICATIONS_FAILED
# ---------------------------------------------------------------------------

def test_batch_all_fail_returns_500(client, mock_classifier):
    mock_classifier.classify_policy.side_effect = RuntimeError("LLM is down")
    assert client.post("/classify/batch", json=_batch_body(2)).status_code == 500


def test_batch_all_fail_error_code(client, mock_classifier):
    mock_classifier.classify_policy.side_effect = RuntimeError("LLM is down")
    data = client.post("/classify/batch", json=_batch_body(2)).json()
    assert data["error"]["code"] == "ALL_CLASSIFICATIONS_FAILED"


# ---------------------------------------------------------------------------
# l) Every response includes an X-Request-ID header
# ---------------------------------------------------------------------------

def test_health_response_has_request_id(client):
    assert "x-request-id" in client.get("/health").headers


def test_classify_200_has_request_id(client, mock_classifier):
    mock_classifier.classify_policy.return_value = _make_result()
    assert "x-request-id" in client.post("/classify", json=_policy_body()).headers


def test_classify_422_has_request_id(client):
    """X-Request-ID is injected by middleware even for validation error responses."""
    response = client.post("/classify", json={"provider": "claude"})
    assert response.status_code == 422
    assert "x-request-id" in response.headers


def test_batch_200_has_request_id(client, mock_classifier):
    mock_classifier.classify_policy.return_value = _make_result()
    assert "x-request-id" in client.post("/classify/batch", json=_batch_body(1)).headers


def test_404_has_request_id(client):
    assert "x-request-id" in client.get("/does-not-exist").headers


# ---------------------------------------------------------------------------
# m) Unknown route → 404 with structured error JSON
# ---------------------------------------------------------------------------

def test_unknown_route_returns_404(client):
    assert client.get("/nonexistent-endpoint").status_code == 404


def test_unknown_route_returns_error_envelope(client):
    data = client.get("/nonexistent-endpoint").json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_unknown_route_error_message_contains_path(client):
    data = client.get("/no-such-route").json()
    assert "/no-such-route" in data["error"]["message"]
