"""
Regression tests for ClassificationService — public-API focused.

Replaces the legacy test_classifier.py which targeted the removed
sync IAMPolicyClassifier class. All tests use the current async
ClassificationService with fully mocked LLM clients.

Focus: end-to-end classification pipeline for realistic policy shapes,
consistency between providers, and correct error propagation.
"""

import pytest
import httpx
import anthropic
import openai
from unittest.mock import AsyncMock, MagicMock

from src.core.classifier import ClassificationService
from src.models.schemas import ClassificationCategory, ClassificationResult


# ---------------------------------------------------------------------------
# Sample policies
# ---------------------------------------------------------------------------

COMPLIANT_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": "arn:aws:s3:::secure-bucket/*",
            "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}},
        }
    ],
}

INSECURE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}],
}

OVERLY_PERMISSIVE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Action": ["s3:*"], "Resource": "*"}],
}

NEEDS_REVIEW_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject"],
            "Resource": "arn:aws:s3:::my-bucket/*",
        }
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _llm_json(category: str, risk_score: int) -> str:
    return (
        f'{{"category": "{category}", "confidence": 0.9, "risk_score": {risk_score},'
        f'"explanation": "test explanation",'
        f'"recommendations": ["remediation step"],'
        f'"policy_summary": "test policy summary"}}'
    )


def _anthropic_msg(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


def _openai_completion(text: str) -> MagicMock:
    choice = MagicMock()
    choice.message.content = text
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def svc() -> ClassificationService:
    """ClassificationService with both provider clients as AsyncMocks."""
    service = ClassificationService()
    service._anthropic = AsyncMock()
    service._openai = AsyncMock()
    return service


# ---------------------------------------------------------------------------
# All four classification categories — via Claude
# ---------------------------------------------------------------------------

async def test_classifies_compliant_policy(svc):
    svc._anthropic.messages.create = AsyncMock(
        return_value=_anthropic_msg(_llm_json("compliant", 8))
    )
    result = await svc.classify_policy(COMPLIANT_POLICY, provider="claude")
    assert result.category == ClassificationCategory.compliant
    assert result.risk_score < 30


async def test_classifies_insecure_policy(svc):
    svc._anthropic.messages.create = AsyncMock(
        return_value=_anthropic_msg(_llm_json("insecure", 95))
    )
    result = await svc.classify_policy(INSECURE_POLICY, provider="claude")
    assert result.category == ClassificationCategory.insecure
    assert result.risk_score >= 75


async def test_classifies_overly_permissive_policy(svc):
    svc._anthropic.messages.create = AsyncMock(
        return_value=_anthropic_msg(_llm_json("overly_permissive", 60))
    )
    result = await svc.classify_policy(OVERLY_PERMISSIVE_POLICY, provider="claude")
    assert result.category == ClassificationCategory.overly_permissive
    assert 45 <= result.risk_score <= 74


async def test_classifies_needs_review_policy(svc):
    svc._anthropic.messages.create = AsyncMock(
        return_value=_anthropic_msg(_llm_json("needs_review", 30))
    )
    result = await svc.classify_policy(NEEDS_REVIEW_POLICY, provider="claude")
    assert result.category == ClassificationCategory.needs_review
    assert 15 <= result.risk_score <= 44


# ---------------------------------------------------------------------------
# Provider consistency — same JSON, both providers
# ---------------------------------------------------------------------------

async def test_both_providers_return_classification_result(svc):
    json_body = _llm_json("insecure", 90)
    svc._anthropic.messages.create = AsyncMock(
        return_value=_anthropic_msg(json_body)
    )
    claude_result = await svc.classify_policy(INSECURE_POLICY, provider="claude")

    svc._openai.chat.completions.create = AsyncMock(
        return_value=_openai_completion(json_body)
    )
    openai_result = await svc.classify_policy(INSECURE_POLICY, provider="openai")

    assert isinstance(claude_result, ClassificationResult)
    assert isinstance(openai_result, ClassificationResult)
    assert claude_result.category == openai_result.category


async def test_providers_set_correct_provider_used(svc):
    json_body = _llm_json("compliant", 5)
    svc._anthropic.messages.create = AsyncMock(
        return_value=_anthropic_msg(json_body)
    )
    svc._openai.chat.completions.create = AsyncMock(
        return_value=_openai_completion(json_body)
    )
    claude_result = await svc.classify_policy(COMPLIANT_POLICY, provider="claude")
    openai_result = await svc.classify_policy(COMPLIANT_POLICY, provider="openai")

    assert claude_result.provider_used == "claude"
    assert openai_result.provider_used == "openai"


# ---------------------------------------------------------------------------
# API error propagation
# ---------------------------------------------------------------------------

async def test_anthropic_connection_error_propagates(svc):
    req = httpx.Request("POST", "https://api.anthropic.com")
    svc._anthropic.messages.create = AsyncMock(
        side_effect=anthropic.APIConnectionError(request=req)
    )
    with pytest.raises(anthropic.APIConnectionError):
        await svc.classify_policy(COMPLIANT_POLICY, provider="claude")


async def test_openai_connection_error_propagates(svc):
    req = httpx.Request("POST", "https://api.openai.com")
    svc._openai.chat.completions.create = AsyncMock(
        side_effect=openai.APIConnectionError(request=req)
    )
    with pytest.raises(openai.APIConnectionError):
        await svc.classify_policy(COMPLIANT_POLICY, provider="openai")


# ---------------------------------------------------------------------------
# Service accepts any dict (validation is the API layer's responsibility)
# ---------------------------------------------------------------------------

async def test_service_accepts_arbitrary_policy_dict(svc):
    """ClassificationService does not pre-validate the policy; it passes it to the LLM."""
    svc._anthropic.messages.create = AsyncMock(
        return_value=_anthropic_msg(_llm_json("compliant", 5))
    )
    result = await svc.classify_policy({"Statement": []}, provider="claude")
    assert result is not None


# ---------------------------------------------------------------------------
# Unsupported provider
# ---------------------------------------------------------------------------

async def test_unsupported_provider_raises_value_error(svc):
    with pytest.raises(ValueError, match="Unsupported provider"):
        await svc.classify_policy(COMPLIANT_POLICY, provider="huggingface")
