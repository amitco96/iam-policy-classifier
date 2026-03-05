import axios from 'axios';
import type { ClassificationResult } from '../types/api';
import { getSessionId, generateUUID } from './session';

export interface HistoryEntry {
  id: string;
  savedAt: string;
  result: ClassificationResult;
  policyJson: Record<string, unknown>;
}

const client = axios.create({ baseURL: '' });

function sessionUrl(): string {
  return `/api/history/${getSessionId()}`;
}

export async function loadHistory(): Promise<HistoryEntry[]> {
  const { data } = await client.get<HistoryEntry[]>(sessionUrl());
  return data;
}

export async function saveEntry(
  result: ClassificationResult,
  policyJson: Record<string, unknown>,
): Promise<HistoryEntry> {
  const body = {
    entry_id: generateUUID(),
    savedAt: new Date().toISOString(),
    result,
    policy_json: policyJson,
  };
  const { data } = await client.post<HistoryEntry>(sessionUrl(), body);
  return data;
}

export async function deleteEntry(id: string): Promise<void> {
  await client.delete(`${sessionUrl()}/${id}`);
}

export async function clearHistory(): Promise<void> {
  await client.delete(sessionUrl());
}
