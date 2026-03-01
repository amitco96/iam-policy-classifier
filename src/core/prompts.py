"""
LLM prompt templates for IAM policy classification.

IMPROVED_PROMPT_V1 — original two-class (Weak/Strong) prompt, kept for reference.
IMPROVED_PROMPT_V2 — production prompt that requests the full structured JSON
                     consumed by ClassificationResult.
"""

# ---------------------------------------------------------------------------
# V1 — archived, two-class output (Weak / Strong)
# ---------------------------------------------------------------------------

IMPROVED_PROMPT_V1 = """You are a cloud security expert analyzing IAM policies.

Analyze this IAM policy and determine if it is WEAK or STRONG.

CRITICAL: Distinguish between read-only and write permissions when evaluating wildcards.

A WEAK policy has:
- Unrestricted actions: Action = "*" (all services and operations)
- Unrestricted resources: Resource = "*" (all resources in the account)
- Public access: Principal = "*" without restrictive conditions
- Write/modify wildcards on broad resources (e.g., "s3:*" on Resource "*")
- No conditions when dealing with sensitive operations or broad access

A STRONG policy has:
- Specific, limited actions OR read-only wildcards (Describe*, Get*, List*)
- Scoped resources using ARNs (e.g., "arn:aws:s3:::bucket-name/*" or "arn:aws:ec2:region:account:instance/*")
- Conditions that restrict access (MFA required, IP allowlist, time-based)
- Follows principle of least privilege
- No ability to modify, delete, or create critical resources

IMPORTANT DISTINCTIONS:

1. Read-only wildcards (Describe*, Get*, List*) on scoped resources = STRONG
   - These cannot modify or delete resources
   - Appropriate for monitoring, auditing, dashboards
   - Example: "ec2:Describe*" on "arn:aws:ec2:us-east-1:123456789012:instance/*" is STRONG

2. Write wildcards (Put*, Delete*, Create*, Update*, *) = WEAK unless heavily restricted
   - These can modify or delete resources
   - Require strong conditions and narrow scoping

3. Resource scoping:
   - "*" = unrestricted (WEAK)
   - Specific ARN with account/region = scoped (STRONG)
   - Example: "arn:aws:ec2:us-east-1:123456789012:instance/*" is scoped, NOT unrestricted

4. Service wildcards:
   - "s3:*" on Resource "*" = WEAK (can delete buckets across all resources)
   - "s3:Get*" on "arn:aws:s3:::specific-bucket/*" = STRONG (read-only on specific bucket)

Policy to analyze:
{policy_json}

Respond ONLY with valid JSON in this exact format (no markdown, no code blocks):
{{
  "classification": "Weak" or "Strong",
  "reason": "brief explanation citing specific policy elements (actions, resources, conditions) and whether permissions are read-only or write-capable"
}}"""


# ---------------------------------------------------------------------------
# V2 — production prompt, four-class structured output
# ---------------------------------------------------------------------------

IMPROVED_PROMPT_V2 = """You are a cloud security expert analyzing AWS IAM policies.

Analyze the policy below and classify it into one of four security categories.

CATEGORY DEFINITIONS:
- "compliant":          Follows least-privilege. Specific actions, scoped ARN resources,
                        no public access, and appropriate conditions where needed.
- "needs_review":       Minor concerns but not immediately dangerous. Slightly broad
                        permissions on non-sensitive resources, or missing recommended
                        (but not required) conditions.
- "overly_permissive":  Broader access than necessary. Service wildcards (e.g., s3:*),
                        Resource="*" with read-only actions, or unnecessary write
                        permissions without compensating controls.
- "insecure":           Critical security flaws. Principal="*" without both MFA AND
                        IP-restriction conditions (public access), Action="*" (full admin),
                        or Resource="*" with write / delete / modify actions.

EVALUATION RULES (apply in priority order):

1. PUBLIC ACCESS CHECK → insecure
   Principal = "*" without BOTH MFA AND IP-restriction conditions.
   Even read-only public access to company data is a critical vulnerability.

2. UNRESTRICTED ADMIN CHECK → insecure
   Action = "*"  OR  (Resource = "*" with ANY write / delete / modify actions present).

3. OVERLY BROAD CHECK → overly_permissive
   Service wildcards (e.g., s3:*, ec2:*) on unscoped resources, OR
   Resource = "*" with read-only actions only.

4. GOOD PRACTICE CHECK → compliant or needs_review
   Specific actions AND scoped ARNs AND appropriate conditions → compliant.
   Mostly specific but missing some best practices                → needs_review.

RISK SCORE GUIDANCE:
  insecure:           75 – 100
  overly_permissive:  45 – 74
  needs_review:       15 – 44
  compliant:           0 – 14

EXAMPLES:
  Action ["ec2:Describe*"]  Resource "arn:aws:ec2:us-east-1:123:instance/*"
    → compliant (read-only, scoped, no public access)

  Principal "*"  Action "s3:GetObject"  Resource "arn:aws:s3:::company-data/*"
    → insecure (public read access to company data)

  Action "s3:*"  Resource "*"
    → insecure (full S3 admin on all resources)

  Action ["s3:GetObject", "s3:ListBucket"]  Resource "*"  no conditions
    → overly_permissive (read-only but unscoped)

Policy to analyze:
{policy_json}

Respond ONLY with valid JSON (no markdown, no code blocks):
{{
  "category": "compliant" | "needs_review" | "overly_permissive" | "insecure",
  "confidence": <float 0.0–1.0>,
  "risk_score": <integer 0–100>,
  "explanation": "<detailed explanation citing Principal, Action, Resource, and Condition elements and their security implications>",
  "recommendations": ["<actionable fix 1>", "<actionable fix 2>"],
  "policy_summary": "<one sentence: what does this policy actually grant?>"
}}"""
