import type { ClassificationResult, ClassificationCategory } from '../types/api';

// ── Design-system maps ────────────────────────────────────────────────────────

const badgeStyles: Record<ClassificationCategory, string> = {
  compliant: 'bg-green-100 text-green-800',
  needs_review: 'bg-amber-100 text-amber-800',
  overly_permissive: 'bg-orange-100 text-orange-800',
  insecure: 'bg-red-100 text-red-800',
};

const categoryLabels: Record<ClassificationCategory, string> = {
  compliant: 'Compliant',
  needs_review: 'Needs Review',
  overly_permissive: 'Overly Permissive',
  insecure: 'Insecure',
};

const gaugeColors: Record<ClassificationCategory, string> = {
  compliant: '#22c55e',
  needs_review: '#f59e0b',
  overly_permissive: '#f97316',
  insecure: '#ef4444',
};

// ── Category icons ────────────────────────────────────────────────────────────

function CategoryIcon({ category }: { category: ClassificationCategory }) {
  const cls = 'w-4 h-4 shrink-0';
  switch (category) {
    case 'compliant':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth={2.5} strokeLinecap="round"
          strokeLinejoin="round" className={cls} aria-hidden="true">
          <path d="M4.5 12.75l6 6 9-13.5" />
        </svg>
      );
    case 'needs_review':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth={2.5} strokeLinecap="round"
          strokeLinejoin="round" className={cls} aria-hidden="true">
          <path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
        </svg>
      );
    case 'overly_permissive':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth={2.5} strokeLinecap="round"
          strokeLinejoin="round" className={cls} aria-hidden="true">
          <path d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
        </svg>
      );
    case 'insecure':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth={2.5} strokeLinecap="round"
          strokeLinejoin="round" className={cls} aria-hidden="true">
          <path d="M6 18 18 6M6 6l12 12" />
        </svg>
      );
  }
}

// ── Semicircular arc gauge ────────────────────────────────────────────────────
// viewBox 0 0 120 70 | center (60, 65) | r=52 | arc M 8,65 A 52,52 0 0,1 112,65
// semicircle length = π × r ≈ 163.36

const ARC_R = 52;
const ARC_CX = 60;
const ARC_CY = 65;
const ARC_LEN = Math.PI * ARC_R; // ≈ 163.36
const ARC_PATH = `M ${ARC_CX - ARC_R},${ARC_CY} A ${ARC_R},${ARC_R} 0 0,1 ${ARC_CX + ARC_R},${ARC_CY}`;

function RiskGauge({ score, category }: { score: number; category: ClassificationCategory }) {
  const fill = (Math.min(100, Math.max(0, score)) / 100) * ARC_LEN;
  const color = gaugeColors[category] ?? '#6b7280';

  return (
    <svg
      viewBox="0 0 120 70"
      className="w-36 h-auto"
      aria-label={`Risk score: ${score} out of 100`}
    >
      {/* Track */}
      <path d={ARC_PATH} fill="none" stroke="#e5e7eb" strokeWidth="8" strokeLinecap="round" />
      {/* Fill */}
      <path
        d={ARC_PATH}
        fill="none"
        stroke={color}
        strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray={`${fill} ${ARC_LEN}`}
      />
      {/* Score number */}
      <text
        x={ARC_CX}
        y="52"
        textAnchor="middle"
        dominantBaseline="middle"
        fill="#111827"
        style={{ fontSize: '22px', fontWeight: 700, fontFamily: 'inherit' }}
      >
        {score}
      </text>
      {/* "out of 100" label */}
      <text
        x={ARC_CX}
        y="63"
        textAnchor="middle"
        dominantBaseline="middle"
        fill="#9ca3af"
        style={{ fontSize: '9px', fontFamily: 'inherit' }}
      >
        out of 100
      </text>
    </svg>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

interface ResultCardProps {
  result: ClassificationResult;
}

export default function ResultCard({ result }: ResultCardProps) {
  const badgeClass = badgeStyles[result.category] ?? 'bg-gray-100 text-gray-800';
  const badgeLabel = categoryLabels[result.category] ?? result.category;

  return (
    <div className="flex flex-col gap-6">
      {/* Header: badge + provider */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <span className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-semibold ${badgeClass}`}>
          <CategoryIcon category={result.category} />
          {badgeLabel}
        </span>
        <span className="inline-block px-2.5 py-0.5 rounded-full bg-gray-100 text-gray-500 text-xs font-medium tracking-wide">
          {result.provider_used}
        </span>
      </div>

      {/* Risk gauge + confidence */}
      <div className="flex items-center gap-8">
        <div className="flex flex-col items-center gap-1">
          <RiskGauge score={result.risk_score} category={result.category} />
          <p className="text-xs text-gray-500 uppercase tracking-wide">Risk Score</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Confidence</p>
          <p className="text-4xl font-bold text-gray-900">
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
              <li
                key={i}
                className="flex items-start gap-3 bg-white border border-gray-100 rounded-lg px-4 py-3 shadow-sm"
              >
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
