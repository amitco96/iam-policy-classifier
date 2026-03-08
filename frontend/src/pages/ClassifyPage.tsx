import { useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import type { ClassificationResult } from '../types/api';
import { classifyPolicy } from '../utils/api';
import { saveEntry } from '../utils/history';
import ResultCard from '../components/ResultCard';

type Provider = 'claude' | 'openai';

export default function ClassifyPage() {
  const [policyText, setPolicyText] = useState('');
  const [fileName, setFileName] = useState<string | null>(null);
  const [provider, setProvider] = useState<Provider>('claude');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const [policyJson, setPolicyJson] = useState<Record<string, unknown> | null>(null);
  const [isSaved, setIsSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [jsonValid, setJsonValid] = useState<boolean | null>(null);
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
      try { JSON.parse(text); setJsonValid(true); } catch { setJsonValid(false); }
    };
    reader.readAsText(file);
    e.target.value = '';
  }

  async function handleSubmit() {
    setError(null);
    setIsSaved(false);
    setSaveError(null);
    setPolicyJson(null);

    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(policyText);
    } catch {
      setError('Invalid JSON — please check your policy format.');
      return;
    }

    setIsLoading(true);
    setResult(null);
    try {
      const data = await classifyPolicy({ policy_json: parsed, provider });
      setResult(data);
      setPolicyJson(parsed);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Classification failed. Please try again.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSave() {
    if (!result || !policyJson || isSaved || isSaving) return;
    setSaveError(null);
    setIsSaving(true);
    try {
      await saveEntry(result, policyJson);
      setIsSaved(true);
      setShowConfirmation(true);
      setTimeout(() => setShowConfirmation(false), 2000);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to save — please try again.';
      setSaveError(message);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="flex flex-col h-full min-h-screen">
      {/* ── Page header ─────────────────────────────────────────────────── */}
      <header className="px-6 py-5 bg-white/70 backdrop-blur-sm border-b border-gray-100">
        <h1 className="text-2xl font-bold text-gray-900">IAM Policy Classifier</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Analyze AWS IAM policies for security risks and compliance issues.
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
              const text = e.target.value;
              setPolicyText(text);
              setError(null);
              if (text.trim() === '') {
                setJsonValid(null);
              } else {
                try { JSON.parse(text); setJsonValid(true); } catch { setJsonValid(false); }
              }
            }}
            spellCheck={false}
          />

          {/* JSON validity indicator */}
          {jsonValid === true && (
            <p className="flex items-center gap-1 text-xs text-green-600 -mt-2">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth={2.5} strokeLinecap="round"
                strokeLinejoin="round" className="w-3.5 h-3.5" aria-hidden="true">
                <path d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              Valid JSON
            </p>
          )}

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
              <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg"
                fill="none" viewBox="0 0 24 24" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10"
                  stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
            {isLoading ? 'Analyzing...' : 'Classify Policy'}
          </button>

          {/* Inline error */}
          {error && (
            <div className="flex items-start gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2" role="alert">
              <p className="flex-1">{error}</p>
              <button
                type="button"
                onClick={() => setError(null)}
                aria-label="Dismiss error"
                className="shrink-0 text-red-400 hover:text-red-600 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth={2} strokeLinecap="round"
                  strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
                  <path d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div className="w-3/5 bg-white shadow-sm rounded-xl border border-gray-100 p-6 flex flex-col gap-4">
          <h2 className="text-base font-semibold text-gray-800">Result</h2>

          {isLoading ? (
            <div className="flex-1 flex flex-col gap-3 animate-pulse min-h-[300px] pt-2">
              <div className="h-7 bg-gray-200 rounded-lg w-1/3" />
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-5/6" />
              <div className="h-4 bg-gray-200 rounded w-4/6" />
              <div className="h-20 bg-gray-200 rounded-lg w-full mt-2" />
              <div className="h-4 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-2/3" />
            </div>
          ) : result ? (
            <>
              <ResultCard result={result} />

              {/* Save to History */}
              <div className="flex flex-col gap-2 pt-1">
                <div className="flex items-center gap-3">
                  {showConfirmation ? (
                    <span className="inline-flex items-center gap-1.5 text-sm font-medium text-green-600">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth={2.5} strokeLinecap="round"
                        strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
                        <path d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                      Saved!
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={handleSave}
                      disabled={isSaved || isSaving}
                      className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg border focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors disabled:cursor-not-allowed
                        disabled:border-gray-200 disabled:text-gray-400
                        enabled:border-indigo-300 enabled:text-indigo-600 enabled:hover:bg-indigo-50"
                    >
                      {isSaving ? (
                        <>
                          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg"
                            fill="none" viewBox="0 0 24 24" aria-hidden="true">
                            <circle className="opacity-25" cx="12" cy="12" r="10"
                              stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          Saving...
                        </>
                      ) : (
                        <>
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" strokeWidth={2} strokeLinecap="round"
                            strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
                            <path d="M17 3H5a2 2 0 0 0-2 2v16l7-3 7 3V5a2 2 0 0 0-2-2z" />
                          </svg>
                          {isSaved ? 'Already saved' : 'Save to History'}
                        </>
                      )}
                    </button>
                  )}
                </div>
                {saveError && (
                  <p className="text-sm text-red-600" role="alert">
                    Save failed: {saveError}
                  </p>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-300 gap-3 min-h-[300px]">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                strokeWidth={1} stroke="currentColor" className="w-14 h-14" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z" />
              </svg>
              <p className="text-sm text-gray-400">Results will appear here</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
