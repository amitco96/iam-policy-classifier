import axios from 'axios';
import type { PolicyInput, ClassificationResult, BatchPolicyInput, BatchClassificationResult } from '../types/api';

const client = axios.create({ baseURL: '' });

function mapApiError(err: unknown): Error {
  if (axios.isAxiosError(err)) {
    if (!err.response) {
      return new Error('Unable to reach the server. Make sure the app is running.');
    }
    if (err.response.status === 429) {
      return new Error('Too many requests — please wait a moment and try again.');
    }
    return new Error('Classification failed. Please try again.');
  }
  return err instanceof Error ? err : new Error('Classification failed. Please try again.');
}

export async function classifyPolicy(input: PolicyInput): Promise<ClassificationResult> {
  try {
    const { data } = await client.post<ClassificationResult>('/api/classify', input);
    return data;
  } catch (err) {
    throw mapApiError(err);
  }
}

export async function classifyBatch(input: BatchPolicyInput): Promise<BatchClassificationResult> {
  try {
    const { data } = await client.post<BatchClassificationResult>('/api/classify/batch', input);
    return data;
  } catch (err) {
    throw mapApiError(err);
  }
}
