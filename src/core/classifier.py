import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
import openai
import anthropic
from huggingface_hub import InferenceClient


load_dotenv()


class OpenAIClassifier:
    """Classify IAM policies using OpenAI's GPT models."""

    def __init__(self, api_key=None, model="gpt-3.5-turbo"):
        """
        Initialize OpenAI classifier.

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env variable)
            model: Model to use (default: gpt-3.5-turbo)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY in .env file")

        openai.api_key = self.api_key
        self.model = model

    def classify(self, policy_json: str, prompt: str) -> str:
        """
        Classify a policy using OpenAI.

        Args:
            policy_json: The IAM policy as JSON string
            prompt: The prompt template with {policy_json} placeholder

        Returns:
            str: LLM response
        """
        full_prompt = prompt.format(policy_json=policy_json)

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a cloud security expert."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.1
        )

        return response.choices[0].message.content


class ClaudeClassifier:
    """Classify IAM policies using Anthropic's Claude."""

    def __init__(self, api_key=None, model="claude-sonnet-4-5"):
        """
        Initialize Claude classifier.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env variable)
            model: Model to use (default: claude-3-5-sonnet-20241022)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY in .env file")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

    def classify(self, policy_json: str, prompt: str) -> str:
        """
        Classify a policy using Claude.

        Args:
            policy_json: The IAM policy as JSON string
            prompt: The prompt template with {policy_json} placeholder

        Returns:
            str: LLM response
        """
        full_prompt = prompt.format(policy_json=policy_json)

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )

        return message.content[0].text



class IAMPolicyClassifier:
    """
    Main engine for classifying IAM policies using LLMs.
    """

    # Default prompt template
    DEFAULT_PROMPT = """You are a cloud security expert analyzing IAM policies.

Analyze this IAM policy and determine if it is WEAK or STRONG.

A WEAK policy has:
- Overly permissive actions (using "*" for actions or resources)
- No conditions or restrictions
- Broad resource access
- Missing MFA requirements
- Allows public access

A STRONG policy has:
- Specific, limited actions (e.g., "s3:GetObject" instead of "s3:*")
- Scoped resources (not "*")
- Conditions that restrict access (IP allowlist, MFA required, time-based)
- Follows principle of least privilege
- Explicit deny for dangerous operations

Policy to analyze:
{policy_json}

Respond ONLY with valid JSON in this exact format (no markdown, no code blocks):
{{
  "classification": "Weak" or "Strong",
  "reason": "brief explanation of why this policy is classified as such"
}}"""

    def __init__(self, provider="openai", **kwargs):
        """
        Initialize the classifier.

        Args:
            provider: LLM provider ("openai", "claude")
            **kwargs: Provider-specific arguments (api_key, model, etc.)
        """
        self.provider = provider.lower()

        if self.provider == "openai":
            self.llm = OpenAIClassifier(**kwargs)
        elif self.provider == "claude":
            self.llm = ClaudeClassifier(**kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'openai', 'claude', or 'huggingface'")

        self.prompt = self.DEFAULT_PROMPT

    def set_prompt(self, prompt: str):
        """
        Set a custom prompt template.

        Args:
            prompt: Prompt template with {policy_json} placeholder
        """
        self.prompt = prompt

    def classify_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify an IAM policy.

        Args:
            policy: IAM policy as a Python dictionary

        Returns:
            dict: Classification result with policy, classification, and reason
        """
        # Convert policy to formatted JSON string
        policy_json = json.dumps(policy, indent=2)

        # Get LLM response
        print(f"Calling {self.provider} API...")
        llm_response = self.llm.classify(policy_json, self.prompt)

        # Parse the response
        classification_result = self._parse_llm_response(llm_response)

        # Build final output
        result = {
            "policy": policy,
            "classification": classification_result["classification"],
            "reason": classification_result["reason"]
        }

        return result

    def _parse_llm_response(self, response: str) -> Dict[str, str]:
        """
        Parse LLM response to extract classification and reason.

        Args:
            response: Raw LLM response

        Returns:
            dict: Parsed classification and reason
        """
        # Clean the response (remove markdown code blocks if present)
        cleaned = response.strip()

        # Remove markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            # Try to parse as JSON
            result = json.loads(cleaned)

            # Validate required fields
            if "classification" not in result or "reason" not in result:
                raise ValueError("Missing required fields")

            # Validate classification value
            if result["classification"] not in ["Weak", "Strong"]:
                raise ValueError(f"Invalid classification: {result['classification']}")

            return result

        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Raw response: {response}")
            raise ValueError("LLM did not return valid JSON")

