export type ClassificationCategory =
  | 'compliant'
  | 'needs_review'
  | 'overly_permissive'
  | 'insecure';

export interface PolicyInput {
  policy_json: Record<string, unknown>;
  provider?: string;
}

export interface ClassificationResult {
  category: ClassificationCategory;
  confidence: number;
  risk_score: number;
  explanation: string;
  recommendations: string[];
  provider_used: string;
  analyzed_at: string;
}

export interface BatchPolicyInput {
  policies: PolicyInput[];
}

export interface BatchClassificationResult {
  results: Array<ClassificationResult | { error: string }>;
  total: number;
  successful: number;
  failed: number;
}
