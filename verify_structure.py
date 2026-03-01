"""
Verify that the project structure and imports are working correctly.
"""
import sys
from pathlib import Path

print("=" * 80)
print("VERIFYING PROJECT STRUCTURE")
print("=" * 80)

try:
    # Test core classifier imports
    print("\n✓ Testing src.core.classifier imports...")
    from src.core.classifier import ClassificationService
    print("  - ClassificationService: OK")

    # Test core prompts imports
    print("\n✓ Testing src.core.prompts imports...")
    from src.core.prompts import IMPROVED_PROMPT_V1, IMPROVED_PROMPT_V2
    print("  - IMPROVED_PROMPT_V1: OK")
    print("  - IMPROVED_PROMPT_V2: OK")

    # Test test policies imports
    print("\n✓ Testing tests.test_policies imports...")
    from tests.test_policies import ASSIGNMENT_POLICIES, EXTENDED_POLICIES
    print(f"  - ASSIGNMENT_POLICIES: OK ({len(ASSIGNMENT_POLICIES)} policies)")
    print(f"  - EXTENDED_POLICIES: OK ({len(EXTENDED_POLICIES)} policies)")

    # Test configuration imports
    print("\n✓ Testing src.config imports...")
    from src.config import settings, validate_settings
    print("  - settings: OK")
    print("  - validate_settings: OK")
    print(f"  - Environment: {settings.ENVIRONMENT}")
    print(f"  - Available LLM providers: {', '.join(settings.get_available_providers())}")

    # Test models imports
    print("\n✓ Testing src.models.schemas imports...")
    from src.models.schemas import (
        PolicyInput,
        ClassificationCategory,
        ClassificationResult,
        BatchPolicyInput,
        BatchClassificationResult,
        HealthResponse,
        ErrorResponse
    )
    print("  - PolicyInput: OK")
    print("  - ClassificationCategory: OK")
    print("  - ClassificationResult: OK")
    print("  - BatchPolicyInput: OK")
    print("  - BatchClassificationResult: OK")
    print("  - HealthResponse: OK")
    print("  - ErrorResponse: OK")

    # Test API imports
    print("\n✓ Testing src.api imports...")
    from src.api import app
    print("  - FastAPI app: OK")

    # Skip old test file (needs rewrite for async)
    print("\n⚠ Skipping tests.test_classifier (will be rewritten for async service in Week 2)")

    print("\n" + "=" * 80)
    print("✓ ALL IMPORTS SUCCESSFUL - Project structure is valid!")
    print("=" * 80)

    # Verify directory structure
    print("\nProject Structure:")
    dirs = ["src/", "src/api/", "src/core/", "src/models/", "src/config/", "src/utils/", "tests/"]
    for d in dirs:
        if Path(d).exists():
            print(f"  ✓ {d}")
        else:
            print(f"  ✗ {d} (missing)")

    # Verify key files
    print("\nKey Files:")
    files = [
        "src/core/classifier.py",
        "src/core/prompts.py",
        "src/config/settings.py",
        "src/models/schemas.py",
        "src/api/main.py",
        "tests/test_policies.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
        "CLAUDE.md"
    ]
    for f in files:
        if Path(f).exists():
            print(f"  ✓ {f}")
        else:
            print(f"  ✗ {f} (missing)")

except ImportError as e:
    print(f"\n✗ Import Error: {e}")
    print("\nMake sure dependencies are installed:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

except Exception as e:
    print(f"\n✗ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)