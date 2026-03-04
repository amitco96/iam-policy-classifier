import type { ClassificationResult, ClassificationCategory } from '../types/api';

const categoryStyles: Record<ClassificationCategory, string> = {
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

interface ResultCardProps {
  result: ClassificationResult;
}

export default function ResultCard({ result }: ResultCardProps) {
  const badgeClass = categoryStyles[result.category] ?? 'bg-gray-100 text-gray-800';
  const badgeLabel = categoryLabels[result.category] ?? result.category;

  return (
    <div className="flex flex-col gap-5">
      {/* Header row: category badge + provider */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${badgeClass}`}>
          {badgeLabel}
        </span>
        <span className="inline-block px-2 py-0.5 rounded bg-gray-100 text-gray-500 text-xs font-medium">
          {result.provider_used}
        </span>
      </div>

      {/* Risk score + confidence */}
      <div className="flex gap-6">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Risk Score</p>
          <p className="text-4xl font-bold text-gray-900">{result.risk_score}</p>
          <p className="text-xs text-gray-400">out of 100</p>
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
        <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Explanation</p>
        <div className="max-h-40 overflow-y-auto text-sm text-gray-700 leading-relaxed border border-gray-100 rounded p-3 bg-gray-50">
          {result.explanation}
        </div>
      </div>

      {/* Recommendations */}
      {result.recommendations.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Recommendations</p>
          <ol className="list-decimal list-inside space-y-1.5">
            {result.recommendations.map((rec, i) => (
              <li key={i} className="text-sm text-gray-700 leading-snug">
                {rec}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
