import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import type { ClassificationCategory } from '../types/api';
import {
  loadHistory,
  deleteEntry,
  clearHistory,
} from '../utils/history';
import type { HistoryEntry } from '../utils/history';
import {
  RiskGauge,
  CategoryIcon,
  badgeStyles,
  categoryLabels,
} from '../components/ResultCard';

// ── Helpers ───────────────────────────────────────────────────────────────────

const riskColors: Record<ClassificationCategory, string> = {
  compliant: '#22c55e',
  needs_review: '#f59e0b',
  overly_permissive: '#f97316',
  insecure: '#ef4444',
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

// ── Expanded detail view ──────────────────────────────────────────────────────

function EntryDetail({
  entry,
  onDelete,
}: {
  entry: HistoryEntry;
  onDelete: () => void;
}) {
  const { result } = entry;
  return (
    <div className="flex flex-col gap-5 pt-4 border-t border-gray-100 mt-4">
      {/* Gauge + confidence */}
      <div className="flex items-center gap-8">
        <div className="flex flex-col items-center gap-0.5">
          <RiskGauge score={result.risk_score} category={result.category} />
          <p className="text-xs text-gray-500 uppercase tracking-wide">Risk Score</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Confidence</p>
          <p className="text-3xl font-bold text-gray-900">
            {Math.round(result.confidence * 100)}%
          </p>
        </div>
      </div>

      {/* Explanation */}
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Explanation</p>
        <div className="text-sm text-gray-700 leading-relaxed bg-gray-50 rounded-lg p-4">
          {result.explanation}
        </div>
      </div>

      {/* Recommendations */}
      {result.recommendations.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-3">Recommendations</p>
          <ol className="flex flex-col gap-2">
            {result.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-3 bg-white border border-gray-100 rounded-lg px-4 py-3 shadow-sm">
                <span className="flex items-center justify-center w-6 h-6 shrink-0 rounded-full bg-indigo-600 text-white text-xs font-bold mt-0.5">
                  {i + 1}
                </span>
                <span className="text-sm text-gray-700 leading-snug">{rec}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Delete */}
      <div>
        <button
          type="button"
          onClick={onDelete}
          className="text-sm font-medium text-red-500 hover:text-red-700 focus:outline-none focus:underline transition-colors"
        >
          Delete this entry
        </button>
      </div>
    </div>
  );
}

// ── Single history row ────────────────────────────────────────────────────────

function HistoryRow({
  entry,
  isExpanded,
  onToggle,
  onDelete,
}: {
  entry: HistoryEntry;
  isExpanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
}) {
  const { result } = entry;
  const badgeClass = badgeStyles[result.category] ?? 'bg-gray-100 text-gray-800';
  const badgeLabel = categoryLabels[result.category] ?? result.category;
  const scoreColor = riskColors[result.category] ?? '#6b7280';
  const policySummary = result.policy_summary ?? JSON.stringify(entry.policyJson);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 px-4 py-3">
      {/* Compact row — click anywhere to expand */}
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center gap-4 text-left focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-inset rounded"
        aria-expanded={isExpanded}
      >
        {/* LEFT: badge + summary */}
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold shrink-0 ${badgeClass}`}>
            <CategoryIcon category={result.category} />
            {badgeLabel}
          </span>
          <span className="text-sm text-gray-600 truncate">{policySummary}</span>
        </div>

        {/* MIDDLE: risk score + provider */}
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-lg font-bold" style={{ color: scoreColor }}>
            {result.risk_score}
          </span>
          <span className="text-xs text-gray-400 font-medium">/ 100</span>
          <span className="ml-1 px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 text-xs font-medium">
            {result.provider_used}
          </span>
        </div>

        {/* RIGHT: date + chevron */}
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-gray-400">{formatDate(entry.savedAt)}</span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
            className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            aria-hidden="true"
          >
            <path d="m6 9 6 6 6-6" />
          </svg>
        </div>
      </button>

      {/* Expanded detail */}
      {isExpanded && (
        <EntryDetail entry={entry} onDelete={onDelete} />
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function HistoryPage() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<HistoryEntry[]>(() => loadHistory());
  const [searchText, setSearchText] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<ClassificationCategory | ''>('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filteredEntries = useMemo(() => {
    const lowerSearch = searchText.toLowerCase();
    return entries.filter(entry => {
      const matchesCategory =
        categoryFilter === '' || entry.result.category === categoryFilter;
      const matchesSearch =
        searchText === '' ||
        JSON.stringify(entry.policyJson).toLowerCase().includes(lowerSearch);
      return matchesCategory && matchesSearch;
    });
  }, [entries, searchText, categoryFilter]);

  function handleDelete(id: string) {
    deleteEntry(id);
    setEntries(loadHistory());
    if (expandedId === id) setExpandedId(null);
  }

  function handleClearAll() {
    if (!window.confirm('Delete all saved classifications? This cannot be undone.')) return;
    clearHistory();
    setEntries([]);
    setExpandedId(null);
  }

  function toggleExpand(id: string) {
    setExpandedId(prev => (prev === id ? null : id));
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* ── Page header ─────────────────────────────────────────────────── */}
      <header className="px-6 py-5 bg-white/70 backdrop-blur-sm border-b border-gray-100 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Classification History</h1>
          <p className="text-sm text-gray-500 mt-0.5">Your saved IAM policy analyses</p>
        </div>
        {entries.length > 0 && (
          <button
            type="button"
            onClick={handleClearAll}
            className="shrink-0 px-4 py-2 text-sm font-medium text-red-600 border border-red-200 rounded-lg hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-400 transition-colors"
          >
            Clear All
          </button>
        )}
      </header>

      <div className="flex flex-col gap-4 p-6">

        {entries.length === 0 ? (
          /* ── Empty state ──────────────────────────────────────────── */
          <div className="flex flex-col items-center justify-center py-24 gap-4 text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
              strokeWidth={1} stroke="currentColor" className="w-14 h-14 text-gray-300"
              aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>
            <p className="text-base font-medium text-gray-500">No saved classifications yet</p>
            <button
              type="button"
              onClick={() => navigate('/')}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-700 hover:underline focus:outline-none"
            >
              Go to Classify →
            </button>
          </div>
        ) : (
          <>
            {/* ── Search / filter bar ───────────────────────────────── */}
            <div className="flex gap-3">
              <div className="relative flex-1">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth={2} strokeLinecap="round"
                  strokeLinejoin="round"
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
                  aria-hidden="true">
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.3-4.3" />
                </svg>
                <input
                  type="text"
                  placeholder="Search policy content..."
                  value={searchText}
                  onChange={e => setSearchText(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder-gray-400"
                />
              </div>
              <select
                value={categoryFilter}
                onChange={e => setCategoryFilter(e.target.value as ClassificationCategory | '')}
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="">All Categories</option>
                <option value="compliant">Compliant</option>
                <option value="needs_review">Needs Review</option>
                <option value="overly_permissive">Overly Permissive</option>
                <option value="insecure">Insecure</option>
              </select>
            </div>

            {/* ── Entry count ──────────────────────────────────────── */}
            <p className="text-xs text-gray-400">
              {filteredEntries.length === entries.length
                ? `${entries.length} saved classification${entries.length !== 1 ? 's' : ''}`
                : `${filteredEntries.length} of ${entries.length} classifications`}
            </p>

            {/* ── List ─────────────────────────────────────────────── */}
            {filteredEntries.length === 0 ? (
              <p className="text-sm text-gray-400 py-8 text-center">
                No results match your filters.
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {filteredEntries.map(entry => (
                  <HistoryRow
                    key={entry.id}
                    entry={entry}
                    isExpanded={expandedId === entry.id}
                    onToggle={() => toggleExpand(entry.id)}
                    onDelete={() => handleDelete(entry.id)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
