import axios from 'axios';
import type { PolicyInput, ClassificationResult, BatchPolicyInput, BatchClassificationResult } from '../types/api';

const client = axios.create({ baseURL: '' });

export async function classifyPolicy(input: PolicyInput): Promise<ClassificationResult> {
  const { data } = await client.post<ClassificationResult>('/api/classify', input);
  return data;
}

export async function classifyBatch(input: BatchPolicyInput): Promise<BatchClassificationResult> {
  const { data } = await client.post<BatchClassificationResult>('/api/classify/batch', input);
  return data;
}
