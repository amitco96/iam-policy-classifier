import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.classifier import IAMPolicyClassifier, OpenAIClassifier, ClaudeClassifier
from tests.test_policies import ASSIGNMENT_POLICIES, EXTENDED_POLICIES
from src.core.prompts import IMPROVED_PROMPT_V1, IMPROVED_PROMPT_V2


# def test_assignment_policies():
#     """
#     Test the 2 assignment-provided policies across all providers.
#     """
#     providers = ["openai", "claude"]

#
#     print("=" * 100)
#     print("ASSIGNMENT POLICIES TEST - ALL PROVIDERS")
#     print("=" * 100)
#     print(f"\nTesting {len(ASSIGNMENT_POLICIES)} assignment policies across {len(providers)} providers\n")
#
#     # Test each policy
#     for policy_idx, policy in enumerate(ASSIGNMENT_POLICIES, 1):
#         print("\n" + "=" * 100)
#         print(f"POLICY {policy_idx}/{len(ASSIGNMENT_POLICIES)}")
#         print("=" * 100)
#
#         # Show the policy
#         print("\nPolicy:")
#         print(json.dumps(policy, indent=2))
#
#         print("\n" + "-" * 100)
#         print("PROVIDER RESULTS")
#         print("-" * 100)
#
#         # Test with each provider
#         for provider in providers:
#             print(f"\n--- {provider.upper()} ---")
#
#             try:
#                 classifier = IAMPolicyClassifier(provider=provider)
#                 result = classifier.classify_policy(policy)
#
#                 print(f"Classification: {result['classification']}")
#                 print(f"Reason: {result['reason']}")
#
#             except Exception as e:
#                 print(f"ERROR: {str(e)}")
#
#         print("\n" + "-" * 100)
#
#     # Summary table
#     print("\n\n" + "=" * 100)
#     print("SUMMARY - ASSIGNMENT POLICIES")
#     print("=" * 100)
#
#     # Collect all results
#     summary_results = []
#     for policy_idx, policy in enumerate(ASSIGNMENT_POLICIES, 1):
#         policy_results = {"policy_num": policy_idx, "providers": {}}
#
#         for provider in providers:
#             try:
#                 classifier = IAMPolicyClassifier(provider=provider)
#                 result = classifier.classify_policy(policy)
#                 policy_results["providers"][provider] = result["classification"]
#             except:
#                 policy_results["providers"][provider] = "ERROR"
#
#         summary_results.append(policy_results)
#
#     # Print table
#     print(f"\n{'Policy':<10} {'OpenAI':<15} {'Claude':<15} {'HuggingFace':<15}")
#     print("-" * 55)
#     for result in summary_results:
#         policy_num = result["policy_num"]
#         openai_class = result["providers"].get("openai", "N/A")
#         claude_class = result["providers"].get("claude", "N/A")
#         hf_class = result["providers"].get("huggingface", "N/A")
#         print(f"Policy {policy_num:<3} {openai_class:<15} {claude_class:<15} {hf_class:<15}")
#
#     print("\n" + "=" * 100)


# def test_extended_policies():
#     """
#     Test extended policies across all providers.
#     """
#     providers = ["openai", "claude", "huggingface"]
#
#     print("\n\n" + "=" * 100)
#     print("EXTENDED POLICIES TEST - ALL PROVIDERS")
#     print("=" * 100)
#     print(f"\nTesting {len(EXTENDED_POLICIES)} extended policies across {len(providers)} providers\n")
#
#     # Test each policy
#     for policy_idx, policy in enumerate(EXTENDED_POLICIES, 1):
#         print("\n" + "=" * 100)
#         print(f"EXTENDED POLICY {policy_idx}/{len(EXTENDED_POLICIES)}")
#         print("=" * 100)
#
#         # Show the policy
#         print("\nPolicy:")
#         print(json.dumps(policy, indent=2))
#
#         print("\n" + "-" * 100)
#         print("PROVIDER RESULTS")
#         print("-" * 100)
#
#         # Test with each provider
#         for provider in providers:
#             print(f"\n--- {provider.upper()} ---")
#
#             try:
#                 classifier = IAMPolicyClassifier(provider=provider)
#                 result = classifier.classify_policy(policy)
#
#                 print(f"Classification: {result['classification']}")
#                 print(f"Reason: {result['reason']}")
#
#             except Exception as e:
#                 print(f"ERROR: {str(e)}")
#
#         print("\n" + "-" * 100)
#
#     # Summary table
#     print("\n\n" + "=" * 100)
#     print("SUMMARY - EXTENDED POLICIES")
#     print("=" * 100)
#
#     # Collect all results
#     summary_results = []
#     for policy_idx, policy in enumerate(EXTENDED_POLICIES, 1):
#         policy_results = {"policy_num": policy_idx, "providers": {}}
#
#         for provider in providers:
#             try:
#                 classifier = IAMPolicyClassifier(provider=provider)
#                 result = classifier.classify_policy(policy)
#                 policy_results["providers"][provider] = result["classification"]
#             except:
#                 policy_results["providers"][provider] = "ERROR"
#
#         summary_results.append(policy_results)
#
#     # Print table
#     print(f"\n{'Policy':<10} {'OpenAI':<15} {'Claude':<15} {'HuggingFace':<15}")
#     print("-" * 55)
#     for result in summary_results:
#         policy_num = result["policy_num"]
#         openai_class = result["providers"].get("openai", "N/A")
#         claude_class = result["providers"].get("claude", "N/A")
#         hf_class = result["providers"].get("huggingface", "N/A")
#         print(f"Policy {policy_num:<3} {openai_class:<15} {claude_class:<15} {hf_class:<15}")
#
#     print("\n" + "=" * 100)


# def test_all_policies():
#     """
#     Test both assignment and extended policies with all providers.
#     Provides complete overview.
#     """
#     all_policies = ASSIGNMENT_POLICIES + EXTENDED_POLICIES
#     providers = ["openai", "claude", "huggingface"]
#
#     print("=" * 100)
#     print("COMPLETE TEST SUITE - ALL POLICIES, ALL PROVIDERS")
#     print("=" * 100)
#     print(f"\nTesting {len(all_policies)} total policies ({len(ASSIGNMENT_POLICIES)} assignment + {len(EXTENDED_POLICIES)} extended)")
#     print(f"Providers: {', '.join(providers)}\n")
#
#     # Collect all results
#     all_results = []
#
#     for policy_idx, policy in enumerate(all_policies, 1):
#         policy_type = "Assignment" if policy_idx <= len(ASSIGNMENT_POLICIES) else "Extended"
#
#         print(f"\nTesting Policy {policy_idx}/{len(all_policies)} ({policy_type})...")
#
#         policy_results = {
#             "policy_num": policy_idx,
#             "policy_type": policy_type,
#             "providers": {}
#         }
#
#         for provider in providers:
#             try:
#                 classifier = IAMPolicyClassifier(provider=provider)
#                 result = classifier.classify_policy(policy)
#                 policy_results["providers"][provider] = {
#                     "classification": result["classification"],
#                     "reason": result["reason"]
#                 }
#             except Exception as e:
#                 policy_results["providers"][provider] = {
#                     "classification": "ERROR",
#                     "reason": str(e)
#                 }
#
#         all_results.append(policy_results)
#
#     # Print comprehensive summary
#     print("\n\n" + "=" * 100)
#     print("COMPREHENSIVE SUMMARY")
#     print("=" * 100)
#
#     print(f"\n{'Policy':<15} {'Type':<12} {'OpenAI':<15} {'Claude':<15} {'HuggingFace':<15}")
#     print("-" * 72)
#
#     for result in all_results:
#         policy_num = result["policy_num"]
#         policy_type = result["policy_type"]
#         openai_class = result["providers"].get("openai", {}).get("classification", "N/A")
#         claude_class = result["providers"].get("claude", {}).get("classification", "N/A")
#         hf_class = result["providers"].get("huggingface", {}).get("classification", "N/A")
#
#         print(f"Policy {policy_num:<7} {policy_type:<12} {openai_class:<15} {claude_class:<15} {hf_class:<15}")
#
#     print("\n" + "=" * 100)
#
#     # Provider agreement analysis
#     print("\nPROVIDER AGREEMENT ANALYSIS")
#     print("-" * 100)
#
#     full_agreement = 0
#     partial_agreement = 0
#     no_agreement = 0
#
#     for result in all_results:
#         classifications = [
#             result["providers"].get("openai", {}).get("classification"),
#             result["providers"].get("claude", {}).get("classification"),
#             result["providers"].get("huggingface", {}).get("classification")
#         ]
#
#         # Remove errors
#         classifications = [c for c in classifications if c and c != "ERROR"]
#
#         if len(classifications) < 2:
#             continue
#
#         unique_classifications = set(classifications)
#
#         if len(unique_classifications) == 1:
#             full_agreement += 1
#         elif len(unique_classifications) == 2:
#             partial_agreement += 1
#         else:
#             no_agreement += 1
#
#     total_analyzed = full_agreement + partial_agreement + no_agreement
#
#     if total_analyzed > 0:
#         print(f"\nFull agreement (all 3 providers agree): {full_agreement}/{total_analyzed}")
#         print(f"Partial agreement (2 providers agree): {partial_agreement}/{total_analyzed}")
#         print(f"No agreement (all different): {no_agreement}/{total_analyzed}")
#
#     print("\n" + "=" * 100)


# # ============================================================================
# # MAIN EXECUTION
# # ============================================================================

# if __name__ == "__main__":
#
#     # Option 1: Test assignment policies only
#     test_assignment_policies()
#
#     # Option 2: Test extended policies only (uncomment after reviewing assignment results)
#     # test_extended_policies()
#
#     # Option 3: Test everything at once (uncomment for full comparison)
#     # test_all_policies()

def test_assignment_policies():
    """
    Test the 2 assignment-provided policies with default classifier.
    """
    print("=" * 100)
    print("ASSIGNMENT POLICIES TEST")
    print("=" * 100)
    print(f"\nTesting {len(ASSIGNMENT_POLICIES)} assignment policies\n")

    # Create default classifier (uses openai by default)
    classifier = IAMPolicyClassifier()

    print(f"Using provider: {classifier.provider}")
    print(f"Using model: {classifier.llm.model}\n")

    # Test each policy
    for policy_idx, policy in enumerate(ASSIGNMENT_POLICIES, 1):
        print("\n" + "=" * 100)
        print(f"POLICY {policy_idx}/{len(ASSIGNMENT_POLICIES)}")
        print("=" * 100)

        print("\nInput JSON Policy:")
        print(json.dumps(policy, indent=2))

        print("\n" + "-" * 100)

        try:
            result = classifier.classify_policy(policy)

            print("\nExpected AI Output:")
            print(json.dumps(result, indent=2))

        except Exception as e:
            print(f"\nERROR: {str(e)}")

        print("\n" + "-" * 100)

    print("\n" + "=" * 100)


def test_extended_policies():
    """
    Test extended policies with OpenAI and Claude.
    """
    print("\n\n" + "=" * 100)
    print("EXTENDED POLICIES TEST")
    print("=" * 100)
    print(f"\nTesting {len(EXTENDED_POLICIES)} extended policies\n")

    # Create classifiers
    openai_classifier = IAMPolicyClassifier(provider="openai")
    claude_classifier = IAMPolicyClassifier(provider="claude")

    # Test each policy
    for policy_idx, policy in enumerate(EXTENDED_POLICIES, 1):
        print("\n" + "=" * 100)
        print(f"EXTENDED POLICY {policy_idx}/{len(EXTENDED_POLICIES)}")
        print("=" * 100)

        print("\nInput JSON Policy:")
        print(json.dumps(policy, indent=2))

        # Test with OpenAI
        print("\n" + "-" * 100)
        print("OPENAI RESPONSE")
        print("-" * 100)
        print(f"Model: {openai_classifier.llm.model}")

        try:
            result = openai_classifier.classify_policy(policy)
            print("\nExpected AI Output:")
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"\nERROR: {str(e)}")

        # Test with Claude
        print("\n" + "-" * 100)
        print("CLAUDE RESPONSE")
        print("-" * 100)
        print(f"Model: {claude_classifier.llm.model}")

        try:
            result = claude_classifier.classify_policy(policy)
            print("\nExpected AI Output:")
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"\nERROR: {str(e)}")

        print("\n" + "-" * 100)

    print("\n" + "=" * 100)


def test_improved_prompts():
    """
    Compare original vs two improved prompt versions using OpenAI on extended policies.
    This tests the iterative improvement process in fixing misclassifications.
    """
    print("=" * 100)
    print("PROMPT IMPROVEMENT TEST - OpenAI on Extended Policies")
    print("=" * 100)
    print(f"\nTesting {len(EXTENDED_POLICIES)} extended policies")
    print("Comparing: Original -> Improved V1 -> Improved V2\n")

    # Create classifiers with different prompts
    original_classifier = IAMPolicyClassifier(provider="openai")
    improved_v1_classifier = IAMPolicyClassifier(provider="openai")
    improved_v1_classifier.set_prompt(IMPROVED_PROMPT_V1)
    improved_v2_classifier = IAMPolicyClassifier(provider="openai")
    improved_v2_classifier.set_prompt(IMPROVED_PROMPT_V2)

    results = []

    # Test each policy
    for policy_idx, policy in enumerate(EXTENDED_POLICIES, 1):
        print("\n" + "=" * 100)
        print(f"EXTENDED POLICY {policy_idx}/{len(EXTENDED_POLICIES)}")
        print("=" * 100)

        print("\nInput JSON Policy:")
        print(json.dumps(policy, indent=2))

        policy_result = {
            "policy_num": policy_idx,
            "policy": policy,
            "original": {},
            "improved_v1": {},
            "improved_v2": {}
        }

        # Test with original prompt
        print("\n" + "-" * 100)
        print("ORIGINAL PROMPT RESULT")
        print("-" * 100)

        try:
            result = original_classifier.classify_policy(policy)
            print(f"Classification: {result['classification']}")
            print(f"Reason: {result['reason']}")

            policy_result["original"] = {
                "classification": result["classification"],
                "reason": result["reason"]
            }
        except Exception as e:
            print(f"ERROR: {str(e)}")
            policy_result["original"] = {"classification": "ERROR", "reason": str(e)}

        # Test with improved V1 prompt
        print("\n" + "-" * 100)
        print("IMPROVED V1 PROMPT RESULT")
        print("-" * 100)

        try:
            result = improved_v1_classifier.classify_policy(policy)
            print(f"Classification: {result['classification']}")
            print(f"Reason: {result['reason']}")

            policy_result["improved_v1"] = {
                "classification": result["classification"],
                "reason": result["reason"]
            }
        except Exception as e:
            print(f"ERROR: {str(e)}")
            policy_result["improved_v1"] = {"classification": "ERROR", "reason": str(e)}

        # Test with improved V2 prompt
        print("\n" + "-" * 100)
        print("IMPROVED V2 PROMPT RESULT")
        print("-" * 100)

        try:
            result = improved_v2_classifier.classify_policy(policy)
            print(f"Classification: {result['classification']}")
            print(f"Reason: {result['reason']}")

            policy_result["improved_v2"] = {
                "classification": result["classification"],
                "reason": result["reason"]
            }
        except Exception as e:
            print(f"ERROR: {str(e)}")
            policy_result["improved_v2"] = {"classification": "ERROR", "reason": str(e)}

        results.append(policy_result)

    # Summary comparison
    print("\n\n" + "=" * 100)
    print("SUMMARY COMPARISON")
    print("=" * 100)

    print(f"\n{'Policy':<10} {'Original':<15} {'Improved V1':<15} {'Improved V2':<15} {'Expected':<15}")
    print("-" * 70)

    # Expected classifications based on our analysis
    expected = ["Weak", "Weak", "Weak", "Strong", "Strong", "Strong"]

    for idx, result in enumerate(results):
        policy_num = f"Policy {result['policy_num']}"
        orig = result["original"].get("classification", "ERROR")
        impr_v1 = result["improved_v1"].get("classification", "ERROR")
        impr_v2 = result["improved_v2"].get("classification", "ERROR")
        exp = expected[idx]

        print(f"{policy_num:<10} {orig:<15} {impr_v1:<15} {impr_v2:<15} {exp:<15}")

    print("\n" + "=" * 100)
    print("ANALYSIS")
    print("=" * 100)

    # Calculate accuracy for each prompt
    original_correct = sum(1 for i, r in enumerate(results)
                          if r["original"].get("classification") == expected[i])
    improved_v1_correct = sum(1 for i, r in enumerate(results)
                             if r["improved_v1"].get("classification") == expected[i])
    improved_v2_correct = sum(1 for i, r in enumerate(results)
                             if r["improved_v2"].get("classification") == expected[i])

    total = len(EXTENDED_POLICIES)

    print(f"\nOriginal Prompt Accuracy:    {original_correct}/{total} ({100*original_correct/total:.1f}%)")
    print(f"Improved V1 Prompt Accuracy: {improved_v1_correct}/{total} ({100*improved_v1_correct/total:.1f}%)")
    print(f"Improved V2 Prompt Accuracy: {improved_v2_correct}/{total} ({100*improved_v2_correct/total:.1f}%)")

    print(f"\nImprovement V1: {'+' if improved_v1_correct > original_correct else ''}{improved_v1_correct - original_correct}")
    print(f"Improvement V2: {'+' if improved_v2_correct > original_correct else ''}{improved_v2_correct - original_correct}")

    # Detailed policy-by-policy analysis
    print("\n" + "=" * 100)
    print("DETAILED ANALYSIS")
    print("=" * 100)

    for idx, result in enumerate(results):
        orig = result["original"].get("classification", "ERROR")
        v1 = result["improved_v1"].get("classification", "ERROR")
        v2 = result["improved_v2"].get("classification", "ERROR")
        exp = expected[idx]

        # Check if there were any changes
        if not (orig == v1 == v2):
            print(f"\nPolicy {result['policy_num']}:")
            print(f"  Original:    {orig} {'(correct)' if orig == exp else '(incorrect)'}")
            print(f"  Improved V1: {v1} {'(correct)' if v1 == exp else '(incorrect)'}")
            print(f"  Improved V2: {v2} {'(correct)' if v2 == exp else '(incorrect)'}")
            print(f"  Expected:    {exp}")

            # Show progression
            if orig != exp and v1 == exp:
                print(f"  Status: V1 fixed misclassification")
            elif orig != exp and v2 == exp and v1 != exp:
                print(f"  Status: V2 fixed misclassification")
            elif orig == exp and v1 != exp:
                print(f"  Status: V1 broke correct classification")
            elif v1 != exp and v2 == exp:
                print(f"  Status: V2 fixed V1's error")

    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    print("\nPrompt Evolution:")
    print(f"  1. Original Prompt:    {original_correct}/{total} correct")
    print(f"  2. Improved V1:        {improved_v1_correct}/{total} correct (focused on read-only vs write)")
    print(f"  3. Improved V2:        {improved_v2_correct}/{total} correct (added Principal priority)")

    if improved_v2_correct == total:
        print(f"\nFinal Result: Achieved perfect accuracy ({total}/{total}) with Improved V2")

    print("\n" + "=" * 100)

    return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":

    # Option 1: Test assignment policies only
    test_assignment_policies()

    # Option 2: Test extended policies only
    test_extended_policies()

    test_improved_prompts()
