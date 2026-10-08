import React, { useState } from 'react';
import {
  Send,
  Layers,
  Sparkles,
  Copy,
  Check,
  Code2,
} from 'lucide-react';
import { DecisionBadge } from '../components/DecisionBadge';
import { ModerationResponse, ModerationEvent, BatchModerationResponse } from '../types';
import { apiClient } from '../api/client';

interface LiveModerationPageProps {
  onNewEvent: (event: ModerationEvent) => void;
}

export const LiveModerationPage: React.FC<LiveModerationPageProps> = ({ onNewEvent }) => {
  const [activeTab, setActiveTab] = useState<'single' | 'batch'>('single');

  // Single mode state
  const [inputText, setInputText] = useState('');
  const [strictMode, setStrictMode] = useState(false);
  const [useBatchQueue, setUseBatchQueue] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [result, setResult] = useState<ModerationResponse | null>(null);
  const [copiedId, setCopiedId] = useState(false);
  const [showRawJson, setShowRawJson] = useState(false);

  // Batch mode state
  const [batchInput, setBatchInput] = useState(
    'Have a wonderful and productive day!\nYou are a complete idiot and should leave.\nI will find where you live and hurt you.\nRunning `kill -9 1234` on production server.'
  );
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResult, setBatchResult] = useState<BatchModerationResponse | null>(null);
  const [batchError, setBatchError] = useState<string | null>(null);

  const sampleChips = [
    { label: 'Benign Greeting', text: 'Hello! I hope everyone is having a great day collaborating on this project.' },
    { label: 'Insult / Abuse', text: 'You are completely incompetent, stupid, and worthless at this job.' },
    { label: 'Violent Threat', text: 'I will hunt you down and destroy your house.' },
    { label: 'Borderline Review', text: 'That person is extremely irritating and should shut up.' },
    { label: 'Computing Kill Command', text: 'Remember to run kill -9 on the hanging PID before restarting daemon.' },
  ];

  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await apiClient.moderateText({
        text: inputText.trim(),
        strict: strictMode,
        use_batch_queue: useBatchQueue,
      });
      setResult(res);

      onNewEvent({
        id: res.request_id || Math.random().toString(36).substring(2, 9),
        timestamp: new Date().toLocaleTimeString(),
        text: inputText.trim(),
        decision: res.decision,
        label: res.label,
        confidence: res.confidence,
        category: res.policy_category || null,
        latencyMs: res.total_latency_ms,
        model: res.model_version,
      });
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Evaluation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBatchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const lines = batchInput
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    if (lines.length === 0) return;

    setBatchLoading(true);
    setBatchError(null);
    try {
      const items = lines.map((text, idx) => ({ text, text_id: `batch-${idx + 1}` }));
      const res = await apiClient.moderateBatch({ items, strict: strictMode });
      setBatchResult(res);

      // Log events
      res.results.forEach((r, idx) => {
        onNewEvent({
          id: r.request_id ? `${r.request_id}-${idx}` : Math.random().toString(36).substring(2, 9),
          timestamp: new Date().toLocaleTimeString(),
          text: lines[idx] || '',
          decision: r.decision,
          label: r.label,
          confidence: r.confidence,
          category: r.policy_category || null,
          latencyMs: r.total_latency_ms,
          model: r.model_version,
        });
      });
    } catch (err: unknown) {
      setBatchError(err instanceof Error ? err.message : 'Batch evaluation failed');
    } finally {
      setBatchLoading(false);
    }
  };

  const copyRequestId = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Mode Navigation Tabs */}
      <div className="flex border-b border-[#37333D] gap-4">
        <button
          onClick={() => setActiveTab('single')}
          className={`pb-3 text-sm font-mono font-medium transition-all relative ${
            activeTab === 'single' ? 'text-[#F5F3F7]' : 'text-[#A8A3AF] hover:text-[#F5F3F7]'
          }`}
        >
          Single Item Real-Time
          {activeTab === 'single' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#A78BFA] to-[#D946EF]" />
          )}
        </button>

        <button
          onClick={() => setActiveTab('batch')}
          className={`pb-3 text-sm font-mono font-medium transition-all relative ${
            activeTab === 'batch' ? 'text-[#F5F3F7]' : 'text-[#A8A3AF] hover:text-[#F5F3F7]'
          }`}
        >
          Vectorized Batch Moderation
          {activeTab === 'batch' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#A78BFA] to-[#D946EF]" />
          )}
        </button>
      </div>

      {activeTab === 'single' ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Input Form Column */}
          <div className="lg:col-span-7 bg-[#1D1B22] border border-[#37333D] rounded-xl p-6">
            <h2 className="text-sm font-bold uppercase tracking-wider text-[#F5F3F7] pb-3 border-b border-[#37333D]/60 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#A78BFA]" />
              Moderation Input Console
            </h2>

            {/* Sample Chips */}
            <div className="mt-4">
              <span className="text-xs font-mono text-[#A8A3AF] block mb-2">Preset Test Payloads:</span>
              <div className="flex flex-wrap gap-1.5">
                {sampleChips.map((chip, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setInputText(chip.text)}
                    className="px-2.5 py-1 rounded bg-[#151419] hover:bg-[#242128] border border-[#37333D] text-[11px] font-mono text-[#A8A3AF] hover:text-[#F5F3F7] transition-colors"
                  >
                    {chip.label}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleSingleSubmit} className="mt-5 space-y-4">
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-mono text-[#A8A3AF]">Content Payload</label>
                  <span className="text-[10px] font-mono text-[#A8A3AF]">
                    {inputText.length} / 512 chars
                  </span>
                </div>
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Type or paste user-generated content here for policy violation inspection..."
                  rows={5}
                  maxLength={512}
                  className="w-full bg-[#151419] border border-[#37333D] focus:border-[#A78BFA] focus:ring-1 focus:ring-[#A78BFA] rounded-lg p-3 text-sm text-[#F5F3F7] placeholder-[#A8A3AF]/40 resize-none font-sans outline-none transition-all"
                />
              </div>

              {/* Options */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-[#151419] border border-[#37333D]/60 text-xs font-mono">
                <label className="flex items-center gap-2 cursor-pointer select-none text-[#F5F3F7]">
                  <input
                    type="checkbox"
                    checked={strictMode}
                    onChange={(e) => setStrictMode(e.target.checked)}
                    className="rounded bg-[#242128] border-[#37333D] text-[#A78BFA] focus:ring-0 focus:ring-offset-0"
                  />
                  <span>Strict Threshold (0.35)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none text-[#F5F3F7]">
                  <input
                    type="checkbox"
                    checked={useBatchQueue}
                    onChange={(e) => setUseBatchQueue(e.target.checked)}
                    className="rounded bg-[#242128] border-[#37333D] text-[#A78BFA] focus:ring-0 focus:ring-offset-0"
                  />
                  <span>Queue via Async Micro-Batcher</span>
                </label>
              </div>

              {errorMsg && (
                <div className="p-3 rounded-lg bg-[#FB7185]/10 border border-[#FB7185]/30 text-xs font-mono text-[#FB7185]">
                  {errorMsg}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setInputText('');
                    setResult(null);
                    setErrorMsg(null);
                  }}
                  className="px-4 py-2 rounded-lg bg-[#151419] hover:bg-[#242128] text-xs font-mono text-[#A8A3AF] border border-[#37333D] transition-colors"
                >
                  Clear
                </button>
                <button
                  type="submit"
                  disabled={loading || !inputText.trim()}
                  className="px-5 py-2 rounded-lg bg-gradient-to-r from-[#A78BFA] to-[#D946EF] hover:opacity-95 text-[#111014] font-semibold text-xs font-mono flex items-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(167,139,250,0.25)]"
                >
                  <Send className="w-3.5 h-3.5" />
                  {loading ? 'Evaluating Model...' : 'Execute Moderation'}
                </button>
              </div>
            </form>
          </div>

          {/* Results Column */}
          <div className="lg:col-span-5 space-y-4">
            <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 min-h-[360px] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-[#37333D]/60">
                  <h2 className="text-sm font-bold uppercase tracking-wider text-[#F5F3F7]">
                    Inference Verdict
                  </h2>
                  {result && (
                    <button
                      onClick={() => setShowRawJson(!showRawJson)}
                      className="text-xs font-mono text-[#A78BFA] hover:text-[#F5F3F7] flex items-center gap-1"
                    >
                      <Code2 className="w-3.5 h-3.5" />
                      {showRawJson ? 'Hide JSON' : 'Raw JSON'}
                    </button>
                  )}
                </div>

                {!result && !loading && (
                  <div className="py-20 text-center text-xs font-mono text-[#A8A3AF] space-y-2">
                    <p>Awaiting moderation input...</p>
                    <p className="text-[10px] text-[#A8A3AF]/60">
                      Submit text or select a preset test payload on the left.
                    </p>
                  </div>
                )}

                {loading && (
                  <div className="py-20 text-center space-y-3">
                    <div className="w-8 h-8 rounded-full border-2 border-[#A78BFA] border-t-transparent animate-spin mx-auto"></div>
                    <p className="text-xs font-mono text-[#A78BFA]">
                      Running ONNX forward pass on CPU...
                    </p>
                  </div>
                )}

                {result && !loading && (
                  <div className="mt-4 space-y-5">
                    {/* Primary Decision Banner */}
                    <div className="p-4 rounded-xl bg-[#151419] border border-[#37333D] flex items-center justify-between">
                      <span className="text-xs font-mono text-[#A8A3AF]">POLICY OUTCOME</span>
                      <DecisionBadge decision={result.decision} size="lg" />
                    </div>

                    {/* Confidence Meter */}
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs font-mono">
                        <span className="text-[#A8A3AF]">Confidence Probability</span>
                        <span className="text-[#F5F3F7] font-bold">
                          {(result.confidence * 100).toFixed(2)}%
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-[#151419] overflow-hidden p-0.5 border border-[#37333D]">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            result.decision === 'allow'
                              ? 'bg-[#34D399]'
                              : result.decision === 'flag_review'
                              ? 'bg-[#FBBF24]'
                              : 'bg-[#FB7185]'
                          }`}
                          style={{ width: `${Math.min(result.confidence * 100, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Detailed Metadata Grid */}
                    <div className="grid grid-cols-2 gap-3 text-xs font-mono pt-2 border-t border-[#37333D]/40">
                      <div className="p-2.5 rounded-lg bg-[#151419] border border-[#37333D]/50">
                        <span className="text-[10px] text-[#A8A3AF] block">INFERRED LABEL</span>
                        <span className="text-[#F5F3F7] font-bold uppercase">{result.label}</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#151419] border border-[#37333D]/50">
                        <span className="text-[10px] text-[#A8A3AF] block">TOTAL LATENCY</span>
                        <span className="text-[#34D399] font-bold">
                          {result.total_latency_ms.toFixed(2)} ms
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#151419] border border-[#37333D]/50">
                        <span className="text-[10px] text-[#A8A3AF] block">INFERENCE TIME</span>
                        <span className="text-[#A78BFA] font-bold">
                          {result.inference_ms.toFixed(2)} ms
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#151419] border border-[#37333D]/50">
                        <span className="text-[10px] text-[#A8A3AF] block">MODEL VERSION</span>
                        <span className="text-[#F5F3F7] font-semibold truncate block">
                          {result.model_version}
                        </span>
                      </div>
                    </div>

                    {/* Categories Tags */}
                    <div>
                      <span className="text-[10px] font-mono text-[#A8A3AF] block mb-1.5">
                        FLAGGED POLICY CATEGORIES
                      </span>
                      {result.policy_categories.length > 0 ? (
                        <div className="flex flex-wrap gap-1.5">
                          {result.policy_categories.map((cat, i) => (
                            <span
                              key={i}
                              className="px-2 py-0.5 rounded text-[11px] font-mono uppercase bg-[#FB7185]/15 text-[#FB7185] border border-[#FB7185]/30 font-semibold"
                            >
                              {cat}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs font-mono text-[#34D399]">
                          No policy violations detected
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Request ID footer */}
              {result && (
                <div className="mt-4 pt-3 border-t border-[#37333D]/40 flex items-center justify-between text-xs font-mono text-[#A8A3AF]">
                  <span className="truncate max-w-[200px]" title={result.request_id}>
                    ID: {result.request_id}
                  </span>
                  <button
                    onClick={() => copyRequestId(result.request_id)}
                    className="flex items-center gap-1 text-[#A78BFA] hover:text-[#F5F3F7] transition-colors"
                  >
                    {copiedId ? <Check className="w-3.5 h-3.5 text-[#34D399]" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedId ? 'Copied' : 'Copy ID'}</span>
                  </button>
                </div>
              )}
            </div>

            {/* Optional Raw JSON view */}
            {result && showRawJson && (
              <div className="bg-[#151419] border border-[#37333D] rounded-xl p-4 font-mono text-xs overflow-x-auto">
                <pre className="text-[#A8A3AF]">{JSON.stringify(result, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Batch Moderation View */
        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-[#37333D]/60">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#F5F3F7] flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#A78BFA]" />
                Vectorized Batch Evaluation
              </h2>
              <p className="text-xs text-[#A8A3AF] font-mono mt-0.5">
                Evaluate multiple items concurrently with a single model pass
              </p>
            </div>
            {batchResult && (
              <span className="text-xs font-mono text-[#34D399] font-bold">
                Batch Latency: {batchResult.total_latency_ms.toFixed(2)} ms ({batchResult.batch_size} items)
              </span>
            )}
          </div>

          <form onSubmit={handleBatchSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-[#A8A3AF] mb-1.5">
                Enter multiple texts (one per line, up to 64 items)
              </label>
              <textarea
                value={batchInput}
                onChange={(e) => setBatchInput(e.target.value)}
                rows={5}
                className="w-full bg-[#151419] border border-[#37333D] focus:border-[#A78BFA] focus:ring-1 focus:ring-[#A78BFA] rounded-lg p-3 text-sm text-[#F5F3F7] placeholder-[#A8A3AF]/40 resize-y font-mono outline-none transition-all"
              />
            </div>

            {batchError && (
              <div className="p-3 rounded-lg bg-[#FB7185]/10 border border-[#FB7185]/30 text-xs font-mono text-[#FB7185]">
                {batchError}
              </div>
            )}

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={batchLoading}
                className="px-5 py-2 rounded-lg bg-gradient-to-r from-[#A78BFA] to-[#D946EF] hover:opacity-95 text-[#111014] font-semibold text-xs font-mono flex items-center gap-2 transition-all disabled:opacity-40 shadow-[0_0_15px_rgba(167,139,250,0.25)]"
              >
                <Layers className="w-3.5 h-3.5" />
                {batchLoading ? 'Evaluating Batch...' : 'Submit Batch'}
              </button>
            </div>
          </form>

          {/* Batch Results Table */}
          {batchResult && (
            <div className="mt-6 overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#37333D] text-[#A8A3AF]">
                    <th className="pb-3 font-semibold">#</th>
                    <th className="pb-3 font-semibold">DECISION</th>
                    <th className="pb-3 font-semibold">LABEL</th>
                    <th className="pb-3 font-semibold">TEXT</th>
                    <th className="pb-3 font-semibold">CONFIDENCE</th>
                    <th className="pb-3 font-semibold">CATEGORIES</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#37333D]/40">
                  {batchResult.results.map((res, i) => (
                    <tr key={i} className="hover:bg-[#242128]/50 transition-colors">
                      <td className="py-2.5 text-[#A8A3AF]">{i + 1}</td>
                      <td className="py-2.5">
                        <DecisionBadge decision={res.decision} size="sm" />
                      </td>
                      <td className="py-2.5 uppercase font-semibold text-[#F5F3F7]">
                        {res.label}
                      </td>
                      <td className="py-2.5 text-[#F5F3F7] max-w-sm truncate">
                        {batchInput.split('\n')[i] || `Item ${i + 1}`}
                      </td>
                      <td className="py-2.5 text-[#A78BFA]">
                        {(res.confidence * 100).toFixed(1)}%
                      </td>
                      <td className="py-2.5 text-[#FB7185]">
                        {res.policy_categories.length > 0
                          ? res.policy_categories.join(', ')
                          : 'none'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
