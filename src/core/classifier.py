"""
Classification service for AWS IAM policies.

Routes classification requests to the appropriate LLM provider (Anthropic Claude
or OpenAI GPT-4), parses the structured JSON response, and returns validated
ClassificationResult objects.

Usage:
    from src.core.classifier import ClassificationService

    service = ClassificationService()
    result = await service.classify_policy(policy_dict, provider="claude")
    print(result.category, result.risk_score)
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

import anthropic
import openai

from src.config import settings
from src.core.prompts import IMPROVED_PROMPT_V2
from src.models.schemas import ClassificationCategory, ClassificationResult

logger = logging.getLogger(__name__)

# Fallback risk scores used when the LLM omits the risk_score field.
_DEFAULT_RISK_SCORES: dict[str, int] = {
    "compliant": 10,
    "needs_review": 35,
    "overly_permissive": 65,
    "insecure": 88,
}


class ClassificationService:
    """
    Production-ready async service for classifying AWS IAM policies.

    Supports Anthropic Claude and OpenAI GPT-4. Both async clients are
    initialised at construction time only when the corresponding API key is
    present in settings, so the service can be instantiated in environments
    where only one provider is configured.
    """

    def __init__(self) -> None:
        self._anthropic: Optional[anthropic.AsyncAnthropic] = (
            anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            if settings.has_anthropic_key()
            else None
        )
        self._openai: Optional[openai.AsyncOpenAI] = (
            openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            if settings.has_openai_key()
            else None
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def classify_policy(
        self,
        policy: dict,
        provider: str = "claude",
    ) -> ClassificationResult:
        """
        Main classification method — routes to the appropriate LLM provider.

        Args:
            policy:   The IAM policy JSON document (already parsed to a dict).
            provider: Which LLM backend to use: 'claude' or 'openai'.

        Returns:
            ClassificationResult with category, risk score, and recommendations.

        Raises:
            ValueError: If the requested provider is unsupported or not configured.
            anthropic.APIError / openai.APIError: Propagated on upstream failures.
        """
        logger.info("Classifying policy with %s", provider)

        if provider == "claude":
            return await self._classify_with_anthropic(policy)
        if provider == "openai":
            return await self._classify_with_openai(policy)

        raise ValueError(
            f"Unsupported provider: '{provider}'. "
            f"Configured providers: {settings.get_available_providers()}"
        )

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    async def _classify_with_anthropic(self, policy: dict) -> ClassificationResult:
        """Use Anthropic Claude API for classification."""
        if self._anthropic is None:
            raise ValueError(
                "Anthropic client is not available — ANTHROPIC_API_KEY is not configured."
            )

        prompt = IMPROVED_PROMPT_V2.format(policy_json=json.dumps(policy, indent=2))

        try:
            message = await self._anthropic.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIConnectionError as exc:
            logger.error("Anthropic API connection failed: %s", exc)
            raise
        except anthropic.RateLimitError as exc:
            logger.error("Anthropic rate limit exceeded: %s", exc)
            raise
        except anthropic.APIStatusError as exc:
            logger.error("Anthropic API returned status %s: %s", exc.status_code, exc)
            raise

        raw = message.content[0].text
        parsed = self._parse_llm_response(raw)
        return self._build_result(parsed, provider_used="claude")

    async def _classify_with_openai(self, policy: dict) -> ClassificationResult:
        """Use OpenAI GPT-4 API for classification."""
        if self._openai is None:
            raise ValueError(
                "OpenAI client is not available — OPENAI_API_KEY is not configured."
            )

        prompt = IMPROVED_PROMPT_V2.format(policy_json=json.dumps(policy, indent=2))

        try:
            response = await self._openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a cloud security expert analyzing AWS IAM policies."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except openai.APIConnectionError as exc:
            logger.error("OpenAI API connection failed: %s", exc)
            raise
        except openai.RateLimitError as exc:
            logger.error("OpenAI rate limit exceeded: %s", exc)
            raise
        except openai.APIStatusError as exc:
            logger.error("OpenAI API returned status %s: %s", exc.status_code, exc)
            raise

        raw = response.choices[0].message.content or ""
        parsed = self._parse_llm_response(raw)
        return self._build_result(parsed, provider_used="openai")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_llm_response(self, response_text: str) -> dict:
        """
        Extract a JSON object from a raw LLM response string.

        Handles three common response shapes:
        1. Plain JSON — the ideal case.
        2. JSON wrapped in a markdown code fence (```json ... ``` or ``` ... ```).
        3. JSON embedded inside surrounding prose — found via regex as a fallback.

        Args:
            response_text: Raw string returned by the LLM.

        Returns:
            Parsed dictionary.

        Raises:
            ValueError: If no valid JSON object can be extracted from the response.
        """
        cleaned = response_text.strip()

        # Strip opening code fence line (e.g. "```json\n" or "```\n")
        if cleaned.startswith("```"):
            first_newline = cleaned.find("\n")
            cleaned = cleaned[first_newline + 1:] if first_newline != -1 else cleaned[3:]

        # Strip closing code fence
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Last resort: pull the first complete {...} block from the raw text.
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        logger.error(
            "Could not parse LLM response as JSON. First 400 chars: %s",
            response_text[:400],
        )
        raise ValueError("LLM returned a response that could not be parsed as JSON.")

    def _calculate_risk_score(self, category: str) -> int:
        """
        Map a classification category to a sensible default risk score.

        Used when the LLM omits the risk_score field in its response.

        Args:
            category: One of the ClassificationCategory enum values as a string.

        Returns:
            Integer risk score between 0 and 100.
        """
        return _DEFAULT_RISK_SCORES.get(category, 50)

    def _build_result(self, parsed: dict, provider_used: str) -> ClassificationResult:
        """
        Construct a validated ClassificationResult from a parsed LLM response.

        Applies safe coercion and clamping so callers always receive a well-formed
        object regardless of minor variance in LLM output.

        Args:
            parsed:        Dictionary extracted from the LLM JSON response.
            provider_used: Name of the provider that produced this response.

        Returns:
            Fully validated ClassificationResult instance.
        """
        category_str = str(parsed.get("category", "needs_review")).lower()
        try:
            category = ClassificationCategory(category_str)
        except ValueError:
            logger.warning(
                "LLM returned unrecognised category '%s'; defaulting to 'needs_review'",
                category_str,
            )
            category = ClassificationCategory.needs_review

        raw_risk = parsed.get("risk_score")
        risk_score = (
            max(0, min(100, int(raw_risk)))
            if raw_risk is not None
            else self._calculate_risk_score(category.value)
        )

        raw_conf = parsed.get("confidence")
        confidence = (
            max(0.0, min(1.0, float(raw_conf)))
            if raw_conf is not None
            else 0.5
        )

        return ClassificationResult(
            category=category,
            confidence=confidence,
            risk_score=risk_score,
            explanation=parsed.get("explanation", "No explanation provided."),
            recommendations=parsed.get("recommendations", []),
            provider_used=provider_used,
            analyzed_at=datetime.now(timezone.utc),
            policy_summary=parsed.get("policy_summary"),
        )
