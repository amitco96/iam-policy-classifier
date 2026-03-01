#!/usr/bin/env python3
"""
Verification script to test the new project structure.
Run this after installing dependencies: pip install -r requirements.txt
"""

import sys
from pathlib import Path

def verify_imports():
    """Verify that all imports work correctly."""
    print("=" * 80)
    print("VERIFYING PROJECT STRUCTURE")
    print("=" * 80)

    try:
        # Test core imports
        print("\n✓ Testing src.core.classifier imports...")
        from src.core.classifier import IAMPolicyClassifier, OpenAIClassifier, ClaudeClassifier
        print("  - IAMPolicyClassifier: OK")
        print("  - OpenAIClassifier: OK")
        print("  - ClaudeClassifier: OK")

        # Test prompt imports
        print("\n✓ Testing src.core.prompts imports...")
        from src.core.prompts import IMPROVED_PROMPT_V1, IMPROVED_PROMPT_V2
        print("  - IMPROVED_PROMPT_V1: OK")
        print("  - IMPROVED_PROMPT_V2: OK")

        # Test test data imports
        print("\n✓ Testing tests.test_policies imports...")
        from tests.test_policies import ASSIGNMENT_POLICIES, EXTENDED_POLICIES
        print(f"  - ASSIGNMENT_POLICIES: OK ({len(ASSIGNMENT_POLICIES)} policies)")
        print(f"  - EXTENDED_POLICIES: OK ({len(EXTENDED_POLICIES)} policies)")

        # Test configuration imports
        print("\n✓ Testing src.config imports...")
        from src.config import settings, validate_settings
        print(f"  - settings: OK")
        print(f"  - validate_settings: OK")
        print(f"  - Environment: {settings.ENVIRONMENT}")
        print(f"  - Available LLM providers: {', '.join(settings.get_available_providers())}")

        # Test test functions
        print("\n✓ Testing tests.test_classifier imports...")
        from tests.test_classifier import (
            test_assignment_policies,
            test_extended_policies,
            test_improved_prompts
        )
        print("  - test_assignment_policies: OK")
        print("  - test_extended_policies: OK")
        print("  - test_improved_prompts: OK")

        print("\n" + "=" * 80)
        print("✓ ALL IMPORTS SUCCESSFUL - Project structure is valid!")
        print("=" * 80)

        # Verify structure
        print("\nProject Structure:")
        project_root = Path(__file__).parent

        expected_dirs = [
            "src",
            "src/api",
            "src/core",
            "src/models",
            "src/config",
            "src/utils",
            "tests"
        ]

        for dir_path in expected_dirs:
            full_path = project_root / dir_path
            status = "✓" if full_path.exists() else "✗"
            print(f"  {status} {dir_path}/")

        expected_files = [
            "src/core/classifier.py",
            "src/core/prompts.py",
            "src/config/settings.py",
            "tests/test_classifier.py",
            "tests/test_policies.py",
            "requirements.txt",
            ".env.example",
            ".gitignore",
            "README.md",
            "CLAUDE.md"
        ]

        print("\nKey Files:")
        for file_path in expected_files:
            full_path = project_root / file_path
            status = "✓" if full_path.exists() else "✗"
            print(f"  {status} {file_path}")

        return True

    except ImportError as e:
        print(f"\n✗ Import Error: {e}")
        print("\nMake sure dependencies are installed:")
        print("  pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        return False


if __name__ == "__main__":
    success = verify_imports()
    sys.exit(0 if success else 1)
