import { useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import type { ClassificationResult } from '../types/api';
import { classifyPolicy } from '../utils/api';
import ResultCard from '../components/ResultCard';

type Provider = 'claude' | 'openai';

export default function ClassifyPage() {
  const [policyText, setPolicyText] = useState('');
  const [fileName, setFileName] = useState<string | null>(null);
  const [provider, setProvider] = useState<Provider>('claude');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const text = evt.target?.result as string;
      setPolicyText(text);
      setFileName(file.name);
      setError(null);
    };
    reader.readAsText(file);
    e.target.value = '';
  }

  async function handleSubmit() {
    setError(null);

    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(policyText);
    } catch {
      setError('Invalid JSON — please check your policy and try again.');
      return;
    }

    setIsLoading(true);
    setResult(null);
    try {
      const data = await classifyPolicy({ policy_json: parsed, provider });
      setResult(data);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Classification failed. Please try again.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full min-h-screen">
      {/* ── Page header ─────────────────────────────────────────────────── */}
      <header className="px-6 py-5 bg-white/70 backdrop-blur-sm border-b border-gray-100">
        <h1 className="text-2xl font-bold text-gray-900">IAM Policy Classifier</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Analyze AWS IAM policies for security risks and compliance issues
        </p>
      </header>

      {/* ── Split layout ────────────────────────────────────────────────── */}
      <div className="flex flex-1 gap-5 p-6">

        {/* LEFT PANEL */}
        <div className="w-2/5 bg-white shadow-sm rounded-xl border border-gray-100 p-6 flex flex-col gap-4">
          <h2 className="text-base font-semibold text-gray-800">Policy Input</h2>

          {/* Textarea */}
          <textarea
            className="w-full flex-1 min-h-[300px] font-mono text-sm border border-gray-200 rounded-lg p-3 resize-y focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder-gray-400 bg-gray-50/50"
            placeholder={'{\n  "Version": "2012-10-17",\n  "Statement": [...]\n}'}
            value={policyText}
            onChange={(e) => {
              setPolicyText(e.target.value);
              setError(null);
            }}
            spellCheck={false}
          />

          {/* File upload */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors shadow-sm"
            >
              Upload JSON
            </button>
            {fileName && (
              <span className="text-sm text-gray-500 truncate max-w-[200px]" title={fileName}>
                {fileName}
              </span>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,application/json"
              className="hidden"
              onChange={handleFileUpload}
            />
          </div>

          {/* Provider selector */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="provider" className="text-sm font-medium text-gray-700">
              Provider
            </label>
            <select
              id="provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value as Provider)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white shadow-sm"
            >
              <option value="claude">Claude</option>
              <option value="openai">OpenAI</option>
            </select>
          </div>

          {/* Submit button */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isLoading || policyText.trim() === ''}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors shadow-sm"
          >
            {isLoading && (
              <svg
                className="animate-spin h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10"
                  stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
            {isLoading ? 'Classifying...' : 'Classify Policy'}
          </button>

          {/* Inline error */}
          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div className="w-3/5 bg-white shadow-sm rounded-xl border border-gray-100 p-6 flex flex-col gap-4">
          <h2 className="text-base font-semibold text-gray-800">Result</h2>

          {result ? (
            <ResultCard result={result} />
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-300 gap-3 min-h-[300px]">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1}
                stroke="currentColor"
                className="w-14 h-14"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z"
                />
              </svg>
              <p className="text-sm text-gray-400">Results will appear here</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
