"""Test the async ClassificationService."""
import asyncio
from src.core import ClassificationService
from src.models.schemas import ClassificationCategory

# Sample IAM policies
COMPLIANT_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": "arn:aws:s3:::my-specific-bucket/*"
        }
    ]
}

INSECURE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "*",
            "Resource": "*"
        }
    ]
}

async def test_classification():
    """Test async classification with both providers."""
    print("=" * 80)
    print("TESTING CLASSIFICATION SERVICE")
    print("=" * 80)
    
    service = ClassificationService()
    
    # Test 1: Classify compliant policy with Claude
    print("\n✓ Test 1: Classify compliant policy with Claude")
    try:
        result = await service.classify_policy(COMPLIANT_POLICY, provider="claude")
        print(f"  Category: {result.category.value}")
        print(f"  Risk Score: {result.risk_score}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Provider: {result.provider_used}")
        print(f"  Explanation: {result.explanation[:100]}...")
        assert result.category in [ClassificationCategory.compliant, ClassificationCategory.needs_review]
        print("  ✓ PASSED")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
    
    # Test 2: Classify insecure policy with Claude
    print("\n✓ Test 2: Classify insecure policy with Claude")
    try:
        result = await service.classify_policy(INSECURE_POLICY, provider="claude")
        print(f"  Category: {result.category.value}")
        print(f"  Risk Score: {result.risk_score}")
        print(f"  Recommendations: {len(result.recommendations)} provided")
        assert result.category == ClassificationCategory.insecure
        assert result.risk_score >= 75
        print("  ✓ PASSED")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
    
    # Test 3: Classify with OpenAI (if key available)
    print("\n✓ Test 3: Classify with OpenAI")
    try:
        result = await service.classify_policy(COMPLIANT_POLICY, provider="openai")
        print(f"  Category: {result.category.value}")
        print(f"  Provider: {result.provider_used}")
        print("  ✓ PASSED")
    except ValueError as e:
        print(f"  ⚠ SKIPPED: {e}")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
    
    # Test 4: Invalid provider
    print("\n✓ Test 4: Invalid provider error handling")
    try:
        await service.classify_policy(COMPLIANT_POLICY, provider="gemini")
        print("  ✗ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {str(e)[:60]}...")
    
    print("\n" + "=" * 80)
    print("✓ CLASSIFICATION SERVICE TESTS COMPLETE")
    print("=" * 80)

# Run the async tests
if __name__ == "__main__":
    asyncio.run(test_classification())