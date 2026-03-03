"""
Unit tests for ClassificationService (src/core/classifier.py).

All LLM API calls are mocked — no real API keys or network access required.
Covers scenarios a–f from the requirements plus edge cases for the
response-parsing pipeline and result-building helpers.
"""

import pytest
import httpx
import anthropic
import openai
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.core.classifier import ClassificationService
from src.models.schemas import ClassificationCategory, ClassificationResult


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

SAMPLE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject"],
            "Resource": "arn:aws:s3:::my-bucket/*",
        }
    ],
}

# A minimal but fully-populated LLM JSON response.
VALID_LLM_JSON = (
    '{"category": "compliant", "confidence": 0.95, "risk_score": 8,'
    ' "explanation": "Read-only access scoped to a specific bucket.",'
    ' "recommendations": ["Add an MFA condition."],'
    ' "policy_summary": "Grants s3:GetObject on a single named bucket."}'
)


# ---------------------------------------------------------------------------
# Response-builder helpers
# ---------------------------------------------------------------------------

def _anthropic_msg(text: str) -> MagicMock:
    """Fake anthropic.Message with content[0].text."""
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


def _openai_completion(text: str) -> MagicMock:
    """Fake openai ChatCompletion with choices[0].message.content."""
    choice = MagicMock()
    choice.message.content = text
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service() -> ClassificationService:
    """ClassificationService with both provider clients replaced by AsyncMocks."""
    svc = ClassificationService()
    svc._anthropic = AsyncMock()
    svc._openai = AsyncMock()
    return svc


@pytest.fixture
def claude_service(service: ClassificationService) -> ClassificationService:
    """Service whose Anthropic client returns a valid classification response."""
    service._anthropic.messages.create = AsyncMock(
        return_value=_anthropic_msg(VALID_LLM_JSON)
    )
    return service


@pytest.fixture
def openai_service(service: ClassificationService) -> ClassificationService:
    """Service whose OpenAI client returns a valid classification response."""
    service._openai.chat.completions.create = AsyncMock(
        return_value=_openai_completion(VALID_LLM_JSON)
    )
    return service


# ---------------------------------------------------------------------------
# a) classify_policy returns a valid ClassificationResult for a well-formed policy
# ---------------------------------------------------------------------------

async def test_classify_returns_classification_result_instance(claude_service):
    result = await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    assert isinstance(result, ClassificationResult)


async def test_classify_result_values_match_llm_response(claude_service):
    result = await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    assert result.category == ClassificationCategory.compliant
    assert result.confidence == pytest.approx(0.95)
    assert result.risk_score == 8
    assert len(result.recommendations) == 1


# ---------------------------------------------------------------------------
# b) classify_policy correctly handles the "claude" provider
# ---------------------------------------------------------------------------

async def test_classify_claude_calls_anthropic_api(claude_service):
    await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    claude_service._anthropic.messages.create.assert_awaited_once()


async def test_classify_claude_does_not_call_openai(claude_service):
    await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    claude_service._openai.chat.completions.create.assert_not_awaited()


async def test_classify_claude_sets_provider_used(claude_service):
    result = await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    assert result.provider_used == "claude"


# ---------------------------------------------------------------------------
# c) classify_policy correctly handles the "openai" provider
# ---------------------------------------------------------------------------

async def test_classify_openai_calls_openai_api(openai_service):
    await openai_service.classify_policy(SAMPLE_POLICY, provider="openai")
    openai_service._openai.chat.completions.create.assert_awaited_once()


async def test_classify_openai_does_not_call_anthropic(openai_service):
    await openai_service.classify_policy(SAMPLE_POLICY, provider="openai")
    openai_service._anthropic.messages.create.assert_not_awaited()


async def test_classify_openai_sets_provider_used(openai_service):
    result = await openai_service.classify_policy(SAMPLE_POLICY, provider="openai")
    assert result.provider_used == "openai"


async def test_classify_openai_returns_classification_result(openai_service):
    result = await openai_service.classify_policy(SAMPLE_POLICY, provider="openai")
    assert isinstance(result, ClassificationResult)


# ---------------------------------------------------------------------------
# d) classify_policy raises when the LLM returns malformed JSON
# ---------------------------------------------------------------------------

async def test_classify_raises_on_plaintext_response(service):
    service._anthropic.messages.create = AsyncMock(
        return_value=_anthropic_msg("The policy looks fine to me!")
    )
    with pytest.raises(ValueError, match="could not be parsed as JSON"):
        await service.classify_policy(SAMPLE_POLICY, provider="claude")


async def test_classify_raises_on_empty_response(service):
    service._anthropic.messages.create = AsyncMock(
        return_value=_anthropic_msg("")
    )
    with pytest.raises(ValueError, match="could not be parsed as JSON"):
        await service.classify_policy(SAMPLE_POLICY, provider="claude")


async def test_classify_raises_on_truncated_json(service):
    service._anthropic.messages.create = AsyncMock(
        return_value=_anthropic_msg('{"category": "insecure"')  # missing closing brace
    )
    with pytest.raises(ValueError, match="could not be parsed as JSON"):
        await service.classify_policy(SAMPLE_POLICY, provider="claude")


async def test_classify_openai_raises_on_malformed_json(service):
    service._openai.chat.completions.create = AsyncMock(
        return_value=_openai_completion("not json at all")
    )
    with pytest.raises(ValueError, match="could not be parsed as JSON"):
        await service.classify_policy(SAMPLE_POLICY, provider="openai")


# ---------------------------------------------------------------------------
# e) classify_policy raises when the LLM API call fails (network error)
# ---------------------------------------------------------------------------

async def test_classify_propagates_anthropic_connection_error(service):
    req = httpx.Request("POST", "https://api.anthropic.com")
    service._anthropic.messages.create = AsyncMock(
        side_effect=anthropic.APIConnectionError(request=req)
    )
    with pytest.raises(anthropic.APIConnectionError):
        await service.classify_policy(SAMPLE_POLICY, provider="claude")


async def test_classify_propagates_openai_connection_error(service):
    req = httpx.Request("POST", "https://api.openai.com")
    service._openai.chat.completions.create = AsyncMock(
        side_effect=openai.APIConnectionError(request=req)
    )
    with pytest.raises(openai.APIConnectionError):
        await service.classify_policy(SAMPLE_POLICY, provider="openai")


async def test_classify_propagates_anthropic_rate_limit_error(service):
    req = httpx.Request("POST", "https://api.anthropic.com")
    resp = httpx.Response(429, request=req, content=b"rate limited")
    service._anthropic.messages.create = AsyncMock(
        side_effect=anthropic.RateLimitError(
            message="Rate limit exceeded", response=resp, body=None
        )
    )
    with pytest.raises(anthropic.RateLimitError):
        await service.classify_policy(SAMPLE_POLICY, provider="claude")


async def test_classify_propagates_openai_rate_limit_error(service):
    req = httpx.Request("POST", "https://api.openai.com")
    resp = httpx.Response(429, request=req, content=b"rate limited")
    service._openai.chat.completions.create = AsyncMock(
        side_effect=openai.RateLimitError(
            message="Rate limit exceeded", response=resp, body=None
        )
    )
    with pytest.raises(openai.RateLimitError):
        await service.classify_policy(SAMPLE_POLICY, provider="openai")


async def test_classify_propagates_anthropic_api_status_error(service):
    req = httpx.Request("POST", "https://api.anthropic.com")
    resp = httpx.Response(500, request=req, content=b"internal error")
    service._anthropic.messages.create = AsyncMock(
        side_effect=anthropic.APIStatusError(
            message="Internal server error", response=resp, body=None
        )
    )
    with pytest.raises(anthropic.APIStatusError):
        await service.classify_policy(SAMPLE_POLICY, provider="claude")


async def test_classify_propagates_openai_api_status_error(service):
    req = httpx.Request("POST", "https://api.openai.com")
    resp = httpx.Response(500, request=req, content=b"internal error")
    service._openai.chat.completions.create = AsyncMock(
        side_effect=openai.APIStatusError(
            message="Internal server error", response=resp, body=None
        )
    )
    with pytest.raises(openai.APIStatusError):
        await service.classify_policy(SAMPLE_POLICY, provider="openai")


# ---------------------------------------------------------------------------
# f) ClassificationResult has all required fields
# ---------------------------------------------------------------------------

async def test_result_has_category_field(claude_service):
    result = await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    assert hasattr(result, "category")
    assert isinstance(result.category, ClassificationCategory)


async def test_result_has_confidence_field(claude_service):
    result = await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    assert hasattr(result, "confidence")
    assert isinstance(result.confidence, float)
    assert 0.0 <= result.confidence <= 1.0


async def test_result_has_risk_score_field(claude_service):
    result = await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    assert hasattr(result, "risk_score")
    assert isinstance(result.risk_score, int)
    assert 0 <= result.risk_score <= 100


async def test_result_has_explanation_field(claude_service):
    result = await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    assert hasattr(result, "explanation")
    assert isinstance(result.explanation, str)
    assert len(result.explanation) > 0


async def test_result_has_recommendations_field(claude_service):
    result = await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    assert hasattr(result, "recommendations")
    assert isinstance(result.recommendations, list)


async def test_result_has_provider_used_field(claude_service):
    result = await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    assert hasattr(result, "provider_used")
    assert isinstance(result.provider_used, str)


async def test_result_has_analyzed_at_field(claude_service):
    result = await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    assert hasattr(result, "analyzed_at")
    assert isinstance(result.analyzed_at, datetime)


async def test_result_has_policy_summary_field(claude_service):
    result = await claude_service.classify_policy(SAMPLE_POLICY, provider="claude")
    assert hasattr(result, "policy_summary")
    # policy_summary is Optional; check it's a string when present
    assert result.policy_summary is None or isinstance(result.policy_summary, str)


# ---------------------------------------------------------------------------
# Provider-not-configured cases
# ---------------------------------------------------------------------------

async def test_classify_claude_not_configured_raises(service):
    service._anthropic = None
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is not configured"):
        await service.classify_policy(SAMPLE_POLICY, provider="claude")


async def test_classify_openai_not_configured_raises(service):
    service._openai = None
    with pytest.raises(ValueError, match="OPENAI_API_KEY is not configured"):
        await service.classify_policy(SAMPLE_POLICY, provider="openai")


async def test_classify_unsupported_provider_raises(service):
    with pytest.raises(ValueError, match="Unsupported provider"):
        await service.classify_policy(SAMPLE_POLICY, provider="gemini")


# ---------------------------------------------------------------------------
# _parse_llm_response — unit tests for the parsing helper
# ---------------------------------------------------------------------------

def test_parse_plain_json():
    svc = ClassificationService()
    result = svc._parse_llm_response('{"category": "compliant", "risk_score": 5}')
    assert result == {"category": "compliant", "risk_score": 5}


def test_parse_markdown_fence_with_language_tag():
    svc = ClassificationService()
    raw = '```json\n{"category": "insecure", "risk_score": 90}\n```'
    result = svc._parse_llm_response(raw)
    assert result["category"] == "insecure"
    assert result["risk_score"] == 90


def test_parse_markdown_fence_without_language_tag():
    svc = ClassificationService()
    raw = '```\n{"category": "compliant", "risk_score": 5}\n```'
    result = svc._parse_llm_response(raw)
    assert result["category"] == "compliant"


def test_parse_json_embedded_in_prose():
    """Regex fallback: JSON found inside surrounding prose text."""
    svc = ClassificationService()
    raw = 'Here is my analysis: {"category": "needs_review", "risk_score": 30} End.'
    result = svc._parse_llm_response(raw)
    assert result["category"] == "needs_review"


def test_parse_raises_on_no_json_at_all():
    svc = ClassificationService()
    with pytest.raises(ValueError, match="could not be parsed as JSON"):
        svc._parse_llm_response("The policy looks fine.")


def test_parse_raises_on_empty_string():
    svc = ClassificationService()
    with pytest.raises(ValueError, match="could not be parsed as JSON"):
        svc._parse_llm_response("")


def test_parse_raises_when_regex_match_is_not_valid_json():
    """Regex finds {…} but content is still not JSON — falls through to ValueError."""
    svc = ClassificationService()
    # Curly braces present so the regex matches, but the content isn't valid JSON.
    with pytest.raises(ValueError, match="could not be parsed as JSON"):
        svc._parse_llm_response("result = {key: value, no quotes}")


# ---------------------------------------------------------------------------
# _build_result — unit tests for the result-building helper
# ---------------------------------------------------------------------------

def _minimal_parsed(
    category: str = "compliant",
    risk_score: int = 10,
    confidence: float = 0.8,
) -> dict:
    return {
        "category": category,
        "confidence": confidence,
        "risk_score": risk_score,
        "explanation": "test explanation",
        "recommendations": ["fix x"],
        "policy_summary": "grants read access",
    }


def test_build_result_clamps_risk_score_above_100():
    svc = ClassificationService()
    parsed = _minimal_parsed(risk_score=150)
    result = svc._build_result(parsed, provider_used="claude")
    assert result.risk_score == 100


def test_build_result_clamps_risk_score_below_0():
    svc = ClassificationService()
    parsed = _minimal_parsed(risk_score=-10)
    result = svc._build_result(parsed, provider_used="claude")
    assert result.risk_score == 0


def test_build_result_clamps_confidence_above_1():
    svc = ClassificationService()
    parsed = _minimal_parsed(confidence=5.0)
    result = svc._build_result(parsed, provider_used="claude")
    assert result.confidence == pytest.approx(1.0)


def test_build_result_clamps_confidence_below_0():
    svc = ClassificationService()
    parsed = _minimal_parsed(confidence=-0.5)
    result = svc._build_result(parsed, provider_used="claude")
    assert result.confidence == pytest.approx(0.0)


def test_build_result_defaults_confidence_when_missing():
    svc = ClassificationService()
    parsed = _minimal_parsed()
    del parsed["confidence"]
    result = svc._build_result(parsed, provider_used="claude")
    assert result.confidence == pytest.approx(0.5)


def test_build_result_uses_fallback_risk_score_when_missing():
    """When risk_score is absent, _calculate_risk_score supplies a category default."""
    svc = ClassificationService()
    parsed = _minimal_parsed(category="insecure")
    del parsed["risk_score"]
    result = svc._build_result(parsed, provider_used="claude")
    assert result.risk_score == 88  # _DEFAULT_RISK_SCORES["insecure"]


def test_build_result_fallback_risk_score_compliant():
    svc = ClassificationService()
    parsed = _minimal_parsed(category="compliant")
    del parsed["risk_score"]
    result = svc._build_result(parsed, provider_used="claude")
    assert result.risk_score == 10


def test_build_result_falls_back_to_needs_review_for_unknown_category():
    svc = ClassificationService()
    parsed = _minimal_parsed(category="totally_unknown")
    result = svc._build_result(parsed, provider_used="claude")
    assert result.category == ClassificationCategory.needs_review


def test_build_result_fills_missing_explanation_with_default():
    svc = ClassificationService()
    parsed = _minimal_parsed()
    del parsed["explanation"]
    result = svc._build_result(parsed, provider_used="claude")
    assert result.explanation == "No explanation provided."


def test_build_result_handles_all_four_categories():
    svc = ClassificationService()
    for cat in ("compliant", "needs_review", "overly_permissive", "insecure"):
        result = svc._build_result(_minimal_parsed(category=cat), provider_used="claude")
        assert result.category == ClassificationCategory(cat)
