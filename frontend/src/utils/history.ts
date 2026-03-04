import type { ClassificationResult } from '../types/api';

export interface HistoryEntry {
  id: string;
  savedAt: string;
  result: ClassificationResult;
  policyJson: Record<string, unknown>;
}

const STORAGE_KEY = 'iam-classifier-history';
const MAX_ENTRIES = 50;

export function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as HistoryEntry[]) : [];
  } catch {
    return [];
  }
}

export function saveEntry(
  result: ClassificationResult,
  policyJson: Record<string, unknown>,
): HistoryEntry {
  const entries = loadHistory();
  const entry: HistoryEntry = {
    id: crypto.randomUUID(),
    savedAt: new Date().toISOString(),
    result,
    policyJson,
  };
  const updated = [entry, ...entries].slice(0, MAX_ENTRIES);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return entry;
}

export function deleteEntry(id: string): void {
  const entries = loadHistory().filter(e => e.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}

export function clearHistory(): void {
  localStorage.removeItem(STORAGE_KEY);
}
