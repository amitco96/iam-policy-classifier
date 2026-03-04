import axios from 'axios';
import type { PolicyInput, ClassificationResult } from '../types/api';

const client = axios.create({ baseURL: '' });

export async function classifyPolicy(input: PolicyInput): Promise<ClassificationResult> {
  const { data } = await client.post<ClassificationResult>('/api/classify', input);
  return data;
}
