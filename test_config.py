#!/usr/bin/env python3
"""
Test script to demonstrate the configuration system.

This script shows how to use the settings module and validates
that the configuration is working correctly.

Run this after setting up your .env file:
    python test_config.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_basic_import():
    """Test that we can import settings."""
    print("=" * 80)
    print("TEST 1: Basic Import")
    print("=" * 80)

    try:
        from src.config import settings
        print("✓ Successfully imported settings")
        return True
    except Exception as e:
        print(f"✗ Failed to import settings: {e}")
        return False


def test_settings_access():
    """Test accessing various settings."""
    print("\n" + "=" * 80)
    print("TEST 2: Settings Access")
    print("=" * 80)

    try:
        from src.config import settings

        # Application metadata
        print(f"\n✓ App Name: {settings.APP_NAME}")
        print(f"✓ Version: {settings.APP_VERSION}")
        print(f"✓ Environment: {settings.ENVIRONMENT}")

        # LLM configuration
        print(f"\n✓ Default LLM Provider: {settings.DEFAULT_LLM_PROVIDER}")
        print(f"✓ Claude Model: {settings.CLAUDE_MODEL}")
        print(f"✓ OpenAI Model: {settings.OPENAI_MODEL}")

        # API keys (check existence, don't print)
        if settings.ANTHROPIC_API_KEY:
            print(f"✓ Anthropic API Key: Configured")
        else:
            print(f"⚠ Anthropic API Key: Not configured")

        if settings.OPENAI_API_KEY:
            print(f"✓ OpenAI API Key: Configured")
        else:
            print(f"⚠ OpenAI API Key: Not configured")

        # Rate limiting
        print(f"\n✓ Rate Limit: {settings.API_RATE_LIMIT} requests per minute")

        # Logging
        print(f"✓ Log Level: {settings.LOG_LEVEL}")

        return True

    except Exception as e:
        print(f"✗ Failed to access settings: {e}")
        return False


def test_helper_methods():
    """Test helper methods."""
    print("\n" + "=" * 80)
    print("TEST 3: Helper Methods")
    print("=" * 80)

    try:
        from src.config import settings

        # Environment checks
        print(f"\n✓ Is Development: {settings.is_development()}")
        print(f"✓ Is Staging: {settings.is_staging()}")
        print(f"✓ Is Production: {settings.is_production()}")

        # API key checks
        print(f"\n✓ Has Anthropic Key: {settings.has_anthropic_key()}")
        print(f"✓ Has OpenAI Key: {settings.has_openai_key()}")
        print(f"✓ Available Providers: {', '.join(settings.get_available_providers())}")

        # Log level
        print(f"\n✓ Numeric Log Level: {settings.get_log_level_int()}")

        # CORS
        print(f"\n✓ CORS Origins: {len(settings.get_cors_origins())} configured")

        return True

    except Exception as e:
        print(f"✗ Helper methods failed: {e}")
        return False


def test_safe_dump():
    """Test safe dumping of settings (with secrets redacted)."""
    print("\n" + "=" * 80)
    print("TEST 4: Safe Configuration Dump")
    print("=" * 80)

    try:
        from src.config import settings

        safe_config = settings.model_dump_safe()

        print("\n✓ Configuration (secrets redacted):")
        print("-" * 80)

        for key, value in sorted(safe_config.items()):
            if key.startswith("_"):
                continue
            print(f"  {key:30} = {value}")

        return True

    except Exception as e:
        print(f"✗ Safe dump failed: {e}")
        return False


def test_validation():
    """Test that validation is working."""
    print("\n" + "=" * 80)
    print("TEST 5: Validation")
    print("=" * 80)

    try:
        from src.config import settings

        # Check that at least one API key is required
        if not settings.has_anthropic_key() and not settings.has_openai_key():
            print("✗ Validation failed: No API keys configured")
            print("  (This should have raised an error during settings initialization)")
            return False

        print("✓ API key validation passed")

        # Check environment validation
        if settings.ENVIRONMENT not in ["development", "staging", "production"]:
            print(f"✗ Invalid environment: {settings.ENVIRONMENT}")
            return False

        print(f"✓ Environment validation passed: {settings.ENVIRONMENT}")

        # Check log level validation
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if settings.LOG_LEVEL not in valid_log_levels:
            print(f"✗ Invalid log level: {settings.LOG_LEVEL}")
            return False

        print(f"✓ Log level validation passed: {settings.LOG_LEVEL}")

        return True

    except Exception as e:
        print(f"✗ Validation test failed: {e}")
        return False


def test_validate_settings_function():
    """Test the validate_settings() function."""
    print("\n" + "=" * 80)
    print("TEST 6: Validate Settings Function")
    print("=" * 80)

    try:
        from src.config import validate_settings

        validate_settings()
        print("\n✓ validate_settings() executed successfully")

        return True

    except Exception as e:
        print(f"✗ validate_settings() failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("=" * 80)
    print("  IAM POLICY CLASSIFIER - CONFIGURATION SYSTEM TEST")
    print("=" * 80)
    print()

    tests = [
        ("Basic Import", test_basic_import),
        ("Settings Access", test_settings_access),
        ("Helper Methods", test_helper_methods),
        ("Safe Dump", test_safe_dump),
        ("Validation", test_validation),
        ("Validate Function", test_validate_settings_function)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {test_name}")

    print("-" * 80)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Configuration system is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Check your configuration.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
