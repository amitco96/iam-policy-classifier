import { useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import JSZip from 'jszip';
import { classifyBatch } from '../utils/api';

type Provider = 'claude' | 'openai';

const MAX_POLICIES = 10;

interface PolicyCard {
  id: string;
  text: string;
  jsonError: string | null;
}

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg"
      fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

export default function BatchPage() {
  const navigate = useNavigate();
  const idRef = useRef(2);
  const jsonInputRef = useRef<HTMLInputElement>(null);
  const zipInputRef = useRef<HTMLInputElement>(null);

  const [cards, setCards] = useState<PolicyCard[]>([
    { id: '1', text: '', jsonError: null },
    { id: '2', text: '', jsonError: null },
  ]);
  const [provider, setProvider] = useState<Provider>('claude');
  const [isLoading, setIsLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [jsonFilesLoaded, setJsonFilesLoaded] = useState<number | null>(null);
  const [zipFilesLoaded, setZipFilesLoaded] = useState<number | null>(null);

  function nextId(): string {
    idRef.current += 1;
    return String(idRef.current);
  }

  function addCard() {
    if (cards.length >= MAX_POLICIES) return;
    setCards(prev => [...prev, { id: nextId(), text: '', jsonError: null }]);
  }

  function removeCard(id: string) {
    if (cards.length <= 1) return;
    setCards(prev => prev.filter(c => c.id !== id));
  }

  function updateCard(id: string, text: string) {
    setCards(prev => prev.map(c => c.id === id ? { ...c, text, jsonError: null } : c));
  }

  function appendTexts(texts: string[]): number {
    // Fill existing empty cards first, then add new ones for the overflow.
    const emptyCards = cards.filter(c => c.text.trim() === '');
    const fillPairs = emptyCards.slice(0, texts.length).map((c, i) => [c.id, texts[i]] as const);
    const fillMap = new Map(fillPairs);
    const fillCount = fillPairs.length;

    const overflow = texts.slice(fillCount);
    const canAdd = MAX_POLICIES - cards.length;
    const newCards = overflow.slice(0, canAdd).map(text => ({ id: nextId(), text, jsonError: null }));

    setCards(prev => [
      ...prev.map(c => fillMap.has(c.id) ? { ...c, text: fillMap.get(c.id)!, jsonError: null } : c),
      ...newCards,
    ]);

    return fillCount + newCards.length;
  }

  function handleJsonFilesUpload(e: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (files.length === 0) return;
    const promises = files.map(
      f => new Promise<string>(resolve => {
        const reader = new FileReader();
        reader.onload = evt => resolve(evt.target?.result as string ?? '');
        reader.readAsText(f);
      })
    );
    Promise.all(promises).then(texts => {
      const added = appendTexts(texts);
      setJsonFilesLoaded(added);
    });
    e.target.value = '';
  }

  async function handleZipUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';
    try {
      const zip = await JSZip.loadAsync(file);
      const jsonEntries = Object.values(zip.files).filter(
        f => !f.dir && f.name.toLowerCase().endsWith('.json')
      );
      const texts = await Promise.all(jsonEntries.map(f => f.async('string')));
      const added = appendTexts(texts);
      setZipFilesLoaded(added);
    } catch {
      // silently ignore corrupt/unreadable zip
    }
  }

  async function handleSubmit() {
    setSubmitError(null);

    let hasError = false;
    const validated = cards.map(card => {
      if (card.text.trim() === '') {
        hasError = true;
        return { ...card, jsonError: 'Policy is empty.' };
      }
      try {
        JSON.parse(card.text);
        return { ...card, jsonError: null };
      } catch {
        hasError = true;
        return { ...card, jsonError: 'Invalid JSON.' };
      }
    });
    setCards(validated);
    if (hasError) return;

    const policies = cards.map(card => ({
      policy_json: JSON.parse(card.text) as Record<string, unknown>,
      provider,
    }));

    setIsLoading(true);
    try {
      const result = await classifyBatch({ policies });
      navigate('/batch/results', { state: { result, policies: cards.map(c => c.text) } });
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : 'Batch analysis failed. Please try again.');
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* ── Page header ─────────────────────────────────────────────────── */}
      <header className="px-6 py-5 bg-white/70 backdrop-blur-sm border-b border-gray-100">
        <h1 className="text-2xl font-bold text-gray-900">Batch Policy Analysis</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Analyze up to 10 IAM policies simultaneously
        </p>
      </header>

      {/* ── Content ─────────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-6 p-6">
        <div className="bg-white shadow-sm rounded-xl border border-gray-100 p-6 flex flex-col gap-5">

          {/* Policy cards */}
          <div className="flex flex-col gap-4">
            {cards.map((card, i) => (
              <div key={card.id} className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Policy #{i + 1}</span>
                  <button
                    type="button"
                    onClick={() => removeCard(card.id)}
                    disabled={cards.length <= 1}
                    aria-label={`Remove policy ${i + 1}`}
                    className="p-1 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                      stroke="currentColor" strokeWidth={2} strokeLinecap="round"
                      strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
                      <path d="M6 18 18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <textarea
                  className={`w-full min-h-[120px] font-mono text-sm border rounded-lg p-3 resize-y focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder-gray-400 bg-gray-50/50 ${
                    card.jsonError ? 'border-red-300' : 'border-gray-200'
                  }`}
                  placeholder={'{\n  "Version": "2012-10-17",\n  "Statement": [...]\n}'}
                  value={card.text}
                  onChange={e => updateCard(card.id, e.target.value)}
                  spellCheck={false}
                />
                {card.jsonError && (
                  <p className="text-xs text-red-600" role="alert">{card.jsonError}</p>
                )}
              </div>
            ))}
          </div>

          {/* Upload row */}
          <div className="flex flex-wrap gap-3 items-center">
            <button
              type="button"
              onClick={() => jsonInputRef.current?.click()}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors shadow-sm"
            >
              Upload JSON Files
            </button>
            <input ref={jsonInputRef} type="file" accept=".json,application/json" multiple
              className="hidden" onChange={handleJsonFilesUpload} />
            {jsonFilesLoaded !== null && (
              <span className="text-sm text-gray-500">
                {jsonFilesLoaded} file{jsonFilesLoaded !== 1 ? 's' : ''} loaded
              </span>
            )}

            <div className="w-px h-5 bg-gray-200" aria-hidden="true" />

            <button
              type="button"
              onClick={() => zipInputRef.current?.click()}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors shadow-sm"
            >
              Upload ZIP
            </button>
            <input ref={zipInputRef} type="file" accept=".zip,application/zip"
              className="hidden" onChange={handleZipUpload} />
            {zipFilesLoaded !== null && (
              <span className="text-sm text-gray-500">
                {zipFilesLoaded} file{zipFilesLoaded !== 1 ? 's' : ''} loaded
              </span>
            )}
          </div>

          {/* Add Policy */}
          {cards.length < MAX_POLICIES && (
            <button
              type="button"
              onClick={addCard}
              className="self-start flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-indigo-600 border border-indigo-300 rounded-lg hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth={2.5} strokeLinecap="round"
                strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
                <path d="M12 5v14M5 12h14" />
              </svg>
              Add Policy
            </button>
          )}

          {/* Provider */}
          <div className="flex flex-col gap-1.5 max-w-xs">
            <label htmlFor="batch-provider" className="text-sm font-medium text-gray-700">
              Provider
            </label>
            <select
              id="batch-provider"
              value={provider}
              onChange={e => setProvider(e.target.value as Provider)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white shadow-sm"
            >
              <option value="claude">Claude</option>
              <option value="openai">OpenAI</option>
            </select>
          </div>

          {/* Submit */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors shadow-sm"
          >
            {isLoading && <Spinner />}
            {isLoading ? 'Analyzing...' : 'Analyze Batch'}
          </button>

          {submitError && (
            <div className="flex items-start gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2" role="alert">
              <p className="flex-1">{submitError}</p>
              <button
                type="button"
                onClick={() => setSubmitError(null)}
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

          {isLoading && (
            <div className="flex flex-col gap-2 animate-pulse pt-1">
              <div className="h-3 bg-gray-200 rounded w-2/3" />
              <div className="h-3 bg-gray-200 rounded w-1/2" />
              <div className="h-3 bg-gray-200 rounded w-3/5" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
