#!/usr/bin/env python3
"""
Example: Using configuration system with the IAM Policy Classifier.

This demonstrates how to integrate the configuration management system
with the existing classification engine.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.core.classifier import IAMPolicyClassifier
from tests.test_policies import ASSIGNMENT_WEAK_POLICY


def example_basic_usage():
    """Example 1: Basic usage with default provider."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Usage with Default Provider")
    print("=" * 80)

    # Get default provider from settings
    print(f"\nDefault LLM Provider: {settings.DEFAULT_LLM_PROVIDER}")
    print(f"Available Providers: {', '.join(settings.get_available_providers())}")

    # Create classifier using default provider from settings
    classifier = IAMPolicyClassifier(provider=settings.DEFAULT_LLM_PROVIDER)

    print(f"\nClassifier initialized with: {classifier.provider}")
    print(f"Using model: {classifier.llm.model}")


def example_provider_selection():
    """Example 2: Dynamic provider selection based on available API keys."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Dynamic Provider Selection")
    print("=" * 80)

    # Get list of available providers based on configured API keys
    available_providers = settings.get_available_providers()

    print(f"\nAvailable providers: {available_providers}")

    # Use the first available provider
    if available_providers:
        provider = available_providers[0]
        print(f"Selected provider: {provider}")

        classifier = IAMPolicyClassifier(provider=provider)
        print(f"✓ Classifier initialized with {provider}")
    else:
        print("✗ No providers available (no API keys configured)")


def example_environment_specific_logic():
    """Example 3: Environment-specific logic."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Environment-Specific Logic")
    print("=" * 80)

    print(f"\nCurrent environment: {settings.ENVIRONMENT}")

    if settings.is_production():
        print("Running in PRODUCTION mode:")
        print("  - Strict CORS origins")
        print("  - Higher rate limits might apply")
        print("  - Enhanced logging")
    elif settings.is_development():
        print("Running in DEVELOPMENT mode:")
        print("  - Relaxed CORS origins")
        print("  - Detailed error messages")
        print("  - Debug logging available")
    else:
        print(f"Running in STAGING mode")


def example_logging_configuration():
    """Example 4: Logging configuration."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Logging Configuration")
    print("=" * 80)

    import logging

    # Configure logging using settings
    logging.basicConfig(
        level=settings.get_log_level_int(),
        format=settings.LOG_FORMAT
    )

    logger = logging.getLogger(__name__)

    print(f"\nLog Level: {settings.LOG_LEVEL}")
    print(f"Numeric Level: {settings.get_log_level_int()}")

    # Test logging at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")

    print("\n✓ Logging configured successfully")


def example_rate_limiting():
    """Example 5: Rate limiting configuration."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Rate Limiting Configuration")
    print("=" * 80)

    print(f"\nRate Limit: {settings.API_RATE_LIMIT} requests per minute")
    print(f"Rate Limit Window: {settings.RATE_LIMIT_WINDOW} seconds")

    print("\nThis configuration will be used by the API layer to:")
    print("  - Limit requests per IP address")
    print("  - Prevent abuse")
    print("  - Ensure fair usage")


def example_full_integration():
    """Example 6: Full integration example."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Full Integration with Existing Classifier")
    print("=" * 80)

    import logging

    # 1. Setup logging
    logging.basicConfig(
        level=settings.get_log_level_int(),
        format=settings.LOG_FORMAT
    )
    logger = logging.getLogger(__name__)

    # 2. Check available providers
    providers = settings.get_available_providers()
    logger.info(f"Available providers: {providers}")

    if not providers:
        logger.error("No LLM providers configured!")
        return

    # 3. Select provider (use default from settings)
    provider = settings.DEFAULT_LLM_PROVIDER

    if provider == "claude" and not settings.has_anthropic_key():
        logger.warning(f"Default provider '{provider}' not available, using fallback")
        provider = providers[0]

    logger.info(f"Using provider: {provider}")

    # 4. Initialize classifier
    try:
        # Get model name from settings
        if provider == "claude":
            model = settings.CLAUDE_MODEL
        elif provider == "openai":
            model = settings.OPENAI_MODEL
        else:
            model = None

        logger.info(f"Initializing classifier with model: {model}")

        # Create classifier
        classifier = IAMPolicyClassifier(provider=provider, model=model)

        # 5. Classify a test policy
        print(f"\n✓ Classifier ready")
        print(f"  Provider: {classifier.provider}")
        print(f"  Model: {classifier.llm.model}")

        # Uncomment to actually run classification (requires API key):
        # result = classifier.classify_policy(ASSIGNMENT_WEAK_POLICY)
        # print(f"\n  Classification: {result['classification']}")
        # print(f"  Reason: {result['reason']}")

    except Exception as e:
        logger.error(f"Failed to initialize classifier: {e}")


def example_configuration_validation():
    """Example 7: Configuration validation on startup."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Configuration Validation on Startup")
    print("=" * 80)

    from src.config import validate_settings

    print("\nValidating configuration...")
    try:
        validate_settings()
        print("\n✓ Configuration is valid and ready to use")
    except Exception as e:
        print(f"\n✗ Configuration validation failed: {e}")


def main():
    """Run all examples."""
    print("\n")
    print("=" * 80)
    print("  CONFIGURATION SYSTEM - USAGE EXAMPLES")
    print("=" * 80)
    print()

    examples = [
        example_basic_usage,
        example_provider_selection,
        example_environment_specific_logic,
        example_logging_configuration,
        example_rate_limiting,
        example_configuration_validation,
        example_full_integration
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n✗ Example failed with error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("EXAMPLES COMPLETE")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  1. Import settings: from src.config import settings")
    print("  2. Access values: settings.ANTHROPIC_API_KEY, settings.LOG_LEVEL")
    print("  3. Use helpers: settings.is_production(), settings.get_available_providers()")
    print("  4. Validate on startup: validate_settings()")
    print("=" * 80)


if __name__ == "__main__":
    main()
