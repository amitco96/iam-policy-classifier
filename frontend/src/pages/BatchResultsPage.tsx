import { useRef, useState, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';
import type {
  BatchClassificationResult,
  ClassificationCategory,
  ClassificationResult,
} from '../types/api';
import {
  RiskGauge,
  CategoryIcon,
  badgeStyles,
  categoryLabels,
} from '../components/ResultCard';

// ── Helpers ───────────────────────────────────────────────────────────────────

const RISK_ORDER: Record<ClassificationCategory, number> = {
  insecure: 4,
  overly_permissive: 3,
  needs_review: 2,
  compliant: 1,
};

function isErrorResult(r: ClassificationResult | { error: string }): r is { error: string } {
  return 'error' in r;
}

// ── Individual result card ────────────────────────────────────────────────────

function BatchResultCard({
  index,
  result,
}: {
  index: number;
  result: ClassificationResult | { error: string };
}) {
  if (isErrorResult(result)) {
    return (
      <div className="bg-white shadow-sm rounded-xl border border-red-100 p-6">
        <p className="text-sm font-semibold text-gray-500 mb-3">Policy #{index + 1}</p>
        <div className="flex items-start gap-3 bg-red-50 rounded-lg p-4">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"
            className="w-5 h-5 text-red-500 shrink-0 mt-0.5" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h.01" />
          </svg>
          <p className="text-sm text-red-700">{result.error}</p>
        </div>
      </div>
    );
  }

  const badgeClass = badgeStyles[result.category] ?? 'bg-gray-100 text-gray-800';
  const badgeLabel = categoryLabels[result.category] ?? result.category;

  return (
    <div className="bg-white shadow-sm rounded-xl border border-gray-100 p-6 flex flex-col gap-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <span className="text-sm font-semibold text-gray-500">Policy #{index + 1}</span>
        <span className="inline-block px-2.5 py-0.5 rounded-full bg-gray-100 text-gray-500 text-xs font-medium tracking-wide">
          {result.provider_used}
        </span>
      </div>

      {/* Badge + gauge + confidence */}
      <div className="flex items-center gap-6 flex-wrap">
        <span className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-semibold ${badgeClass}`}>
          <CategoryIcon category={result.category} />
          {badgeLabel}
        </span>
        <div className="flex items-center gap-6">
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
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

interface LocationState {
  result: BatchClassificationResult;
  policies: string[];
}

export default function BatchResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const contentRef = useRef<HTMLDivElement>(null);
  const [isPdfLoading, setIsPdfLoading] = useState(false);

  const state = location.state as LocationState | null;

  const analyzedAt = useMemo(() => {
    if (!state) return '';
    const firstSuccess = state.result.results.find(r => !isErrorResult(r)) as ClassificationResult | undefined;
    const ts = firstSuccess?.analyzed_at;
    return ts ? new Date(ts).toLocaleString() : new Date().toLocaleString();
  }, [state]);

  // ── No state guard ──────────────────────────────────────────────────────────
  if (!state) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4 text-gray-500">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round"
          className="w-12 h-12 text-gray-300" aria-hidden="true">
          <path d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25Z" />
        </svg>
        <p className="text-lg font-semibold text-gray-700">No results found</p>
        <p className="text-sm text-gray-400">Run a batch analysis to see results here.</p>
        <button
          type="button"
          onClick={() => navigate('/batch')}
          className="mt-2 px-5 py-2.5 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Go Back
        </button>
      </div>
    );
  }

  const { result } = state;
  const successful = result.results.filter(r => !isErrorResult(r)) as ClassificationResult[];

  const avgRisk =
    successful.length > 0
      ? Math.round(successful.reduce((s, r) => s + r.risk_score, 0) / successful.length)
      : null;

  let highestCategory: ClassificationCategory | null = null;
  let highestRiskScore = 0;
  for (const r of successful) {
    const s = RISK_ORDER[r.category] ?? 0;
    if (s > highestRiskScore) { highestRiskScore = s; highestCategory = r.category; }
  }

  async function handleDownloadPdf() {
    if (!contentRef.current) return;
    setIsPdfLoading(true);
    try {
      const canvas = await html2canvas(contentRef.current, {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#f8fafc',
      });
      const imgData = canvas.toDataURL('image/png');
      const pageWidth = 210; // A4 mm
      const pageHeight = 297;
      const imgWidth = pageWidth;
      const imgHeight = (canvas.height * pageWidth) / canvas.width;
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

      let heightLeft = imgHeight;
      let position = 0;
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      pdf.save(`iam-analysis-${timestamp}.pdf`);
    } finally {
      setIsPdfLoading(false);
    }
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* ── Page header ─────────────────────────────────────────────────── */}
      <header className="px-6 py-5 bg-white/70 backdrop-blur-sm border-b border-gray-100">
        <h1 className="text-2xl font-bold text-gray-900">Analysis Results</h1>
        <p className="text-sm text-gray-500 mt-0.5">Analyzed at {analyzedAt}</p>
      </header>

      {/* ── Action bar (excluded from PDF) ──────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-100 gap-3">
        <button
          type="button"
          onClick={() => navigate('/batch')}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 transition-colors shadow-sm"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"
            className="w-4 h-4" aria-hidden="true">
            <path d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
          </svg>
          Back to Batch
        </button>

        <button
          type="button"
          onClick={handleDownloadPdf}
          disabled={isPdfLoading}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors shadow-sm"
        >
          {isPdfLoading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg"
                fill="none" viewBox="0 0 24 24" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Generating PDF...
            </>
          ) : (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"
                className="w-4 h-4" aria-hidden="true">
                <path d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Download PDF
            </>
          )}
        </button>
      </div>

      {/* ── PDF-captured content ─────────────────────────────────────────── */}
      <div ref={contentRef} className="flex flex-col gap-6 p-6">

        {/* Section heading */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Batch Results</h2>
          <hr className="mt-3 border-gray-200" />
        </div>

        {/* Summary bar */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white shadow-sm rounded-xl border border-gray-100 p-4 flex flex-col gap-1">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Total</p>
            <p className="text-3xl font-bold text-gray-900">{result.total}</p>
            <p className="text-xs text-gray-400">policies</p>
          </div>
          <div className="bg-white shadow-sm rounded-xl border border-green-100 p-4 flex flex-col gap-1">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Successful</p>
            <p className="text-3xl font-bold text-green-600">{result.successful}</p>
            <p className="text-xs text-gray-400">analyzed</p>
          </div>
          <div className="bg-white shadow-sm rounded-xl border border-red-100 p-4 flex flex-col gap-1">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Failed</p>
            <p className="text-3xl font-bold text-red-500">{result.failed}</p>
            <p className="text-xs text-gray-400">errors</p>
          </div>
          <div className="bg-white shadow-sm rounded-xl border border-indigo-100 p-4 flex flex-col gap-1">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Avg Risk Score</p>
            <p className="text-3xl font-bold text-indigo-600">
              {avgRisk !== null ? avgRisk : '—'}
            </p>
            <p className="text-xs text-gray-400">out of 100</p>
          </div>
        </div>

        {/* Highest risk category */}
        {highestCategory && (
          <div className="flex items-center gap-3">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Highest Risk Category</p>
            <span className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-semibold ${badgeStyles[highestCategory]}`}>
              <CategoryIcon category={highestCategory} />
              {categoryLabels[highestCategory]}
            </span>
          </div>
        )}

        {/* Individual result cards */}
        <div className="flex flex-col gap-4">
          {result.results.map((r, i) => (
            <BatchResultCard key={i} index={i} result={r} />
          ))}
        </div>

      </div>
    </div>
  );
}
