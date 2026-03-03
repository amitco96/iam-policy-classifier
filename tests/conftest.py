"""
Pytest configuration and shared fixtures.

Environment variables are set at the top of this module — before any src
package is imported — so that the Pydantic Settings singleton (which
validates that at least one API key is present) does not raise on import
during unit tests that mock all LLM calls.
"""
import os

# Must be set before any `from src.*` import, because `src.config.settings`
# is a module-level singleton that validates API keys at instantiation time.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-anthropic-unit-tests")
os.environ.setdefault("OPENAI_API_KEY", "test-key-openai-unit-tests")
