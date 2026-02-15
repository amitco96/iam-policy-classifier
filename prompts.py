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

IMPROVED_PROMPT_V2 = """You are a cloud security expert analyzing IAM policies.

Analyze this IAM policy and determine if it is WEAK or STRONG.

CRITICAL RULES (evaluate in this order):

1. PUBLIC ACCESS CHECK (highest priority):
   - If Principal = "*" without strong conditions (MFA AND IP restrictions) → ALWAYS WEAK
   - Even if actions are read-only and resources are scoped
   - Public access to sensitive data is a critical vulnerability
   - Example: Principal "*" with s3:GetObject on company data = WEAK (public read access)

2. UNRESTRICTED ACCESS CHECK:
   - If Action = "*" (all services) → WEAK
   - If Resource = "*" (all resources) → WEAK
   - These grant unrestricted access across the entire AWS account

3. READ vs WRITE PERMISSIONS:
   - Read-only wildcards (Describe*, Get*, List*) on scoped resources = STRONG
   - Write wildcards (Put*, Delete*, Create*, Update*, Modify*) = WEAK unless heavily restricted
   - Service wildcards (s3:*, ec2:*) = WEAK unless resource is very specific AND read-only

4. RESOURCE SCOPING:
   - Resource = "*" → unrestricted (WEAK)
   - Resource with specific ARN including account/region → scoped (STRONG)
   - Example: "arn:aws:ec2:us-east-1:123456789012:instance/*" is scoped, not "*"

A WEAK policy has ANY of:
- Principal = "*" without both MFA and IP conditions (public access)
- Action = "*" (unrestricted actions)
- Resource = "*" with write-capable actions
- Write/modify wildcards on broad resources
- No conditions when dealing with sensitive operations

A STRONG policy has ALL of:
- No public access (Principal not "*", or if "*" then MFA AND IP required)
- Specific actions OR read-only wildcards (Describe*, Get*, List*)
- Scoped resources (ARNs with account/region/service specified)
- Follows principle of least privilege
- No ability to modify/delete critical resources

IMPORTANT EXAMPLES:

1. Read-only on scoped resource = STRONG:
   Action: ["ec2:Describe*", "ec2:Get*"]
   Resource: "arn:aws:ec2:us-east-1:123456789012:instance/*"
   → STRONG (read-only, scoped, monitoring use case)

2. Read-only but PUBLIC = WEAK:
   Principal: "*"
   Action: "s3:GetObject"
   Resource: "arn:aws:s3:::company-data/*"
   → WEAK (public access to company data, even though read-only)

3. Specific action with MFA and IP = STRONG:
   Action: "s3:GetObject"
   Resource: "arn:aws:s3:::reports/*"
   Condition: MFA required AND IP restrictions
   → STRONG (specific action, scoped, strong conditions)

Policy to analyze:
{policy_json}

Respond ONLY with valid JSON in this exact format (no markdown, no code blocks):
{{
  "classification": "Weak" or "Strong",
  "reason": "brief explanation citing specific policy elements (Principal, actions, resources, conditions) and the security implications"
}}"""