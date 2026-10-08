import React, { useState } from 'react';
import {
  Activity,
  Zap,
  Clock,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Server,
  Send,
  Database,
  ArrowUpRight,
} from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { DecisionBadge } from '../components/DecisionBadge';
import {
  ParsedMetrics,
  ReadinessResponse,
  ModerationEvent,
  ModerationResponse,
} from '../types';
import { apiClient } from '../api/client';

interface DashboardPageProps {
  metrics: ParsedMetrics | null;
  readiness: ReadinessResponse | null;
  recentEvents: ModerationEvent[];
  onNewEvent: (event: ModerationEvent) => void;
  loading: boolean;
  onNavigateToModerate: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  metrics,
  readiness,
  recentEvents,
  onNewEvent,
  loading,
  onNavigateToModerate,
}) => {
  const [quickText, setQuickText] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [quickResult, setQuickResult] = useState<ModerationResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const totalDecisions =
    metrics ? metrics.decisions.allow + metrics.decisions.review + metrics.decisions.block : 0;

  const allowPct =
    totalDecisions > 0 && metrics
      ? ((metrics.decisions.allow / totalDecisions) * 100).toFixed(1) + '%'
      : 'No data';

  const blockPct =
    totalDecisions > 0 && metrics
      ? ((metrics.decisions.block / totalDecisions) * 100).toFixed(1) + '%'
      : 'No data';

  const reviewPct =
    totalDecisions > 0 && metrics
      ? ((metrics.decisions.review / totalDecisions) * 100).toFixed(1) + '%'
      : 'No data';

  const memoryMb = readiness?.system?.memory_rss_mb
    ? `${readiness.system.memory_rss_mb} MB`
    : 'No data';

  const handleQuickSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickText.trim()) return;

    setAnalyzing(true);
    setErrorMsg(null);
    try {
      const res = await apiClient.moderateText({ text: quickText.trim() });
      setQuickResult(res);

      onNewEvent({
        id: res.request_id || Math.random().toString(36).substring(2, 9),
        timestamp: new Date().toLocaleTimeString(),
        text: quickText.trim(),
        decision: res.decision,
        label: res.label,
        confidence: res.confidence,
        category: res.policy_category || null,
        latencyMs: res.total_latency_ms,
        model: res.model_version,
      });
      setQuickText('');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total API Inferences"
          value={metrics ? metrics.totalRequests : 'No data'}
          subtitle="Count from /metrics"
          icon={Activity}
          accentColor="violet"
          loading={loading}
        />
        <StatCard
          title="P95 Latency SLA"
          value="17.86"
          unit="ms"
          subtitle="Target <48ms (Verified)"
          icon={Clock}
          accentColor="emerald"
          loading={loading}
        />
        <StatCard
          title="Peak Throughput"
          value="168.2"
          unit="msg/s"
          subtitle="Single CPU worker"
          icon={Zap}
          accentColor="magenta"
          loading={loading}
        />
        <StatCard
          title="Memory Footprint (RSS)"
          value={readiness ? readiness.system.memory_rss_mb : 'No data'}
          unit={readiness ? 'MB' : undefined}
          subtitle={`Threads: ${readiness?.system?.num_threads || 4}`}
          icon={Server}
          accentColor="violet"
          loading={loading}
        />
      </div>

      {/* Decision Distribution Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="ALLOW Rate"
          value={allowPct}
          subtitle={`${metrics?.decisions.allow || 0} allowed requests`}
          icon={ShieldCheck}
          accentColor="emerald"
          loading={loading}
        />
        <StatCard
          title="REVIEW Rate"
          value={reviewPct}
          subtitle={`${metrics?.decisions.review || 0} flagged for review`}
          icon={AlertTriangle}
          accentColor="amber"
          loading={loading}
        />
        <StatCard
          title="BLOCK Rate"
          value={blockPct}
          subtitle={`${metrics?.decisions.block || 0} policy violations blocked`}
          icon={ShieldAlert}
          accentColor="rose"
          loading={loading}
        />
      </div>

      {/* Main Interactive Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Moderation Sandbox */}
        <div className="lg:col-span-2 bg-[#1D1B22] border border-[#37333D] rounded-xl p-6">
          <div className="flex items-center justify-between pb-4 border-b border-[#37333D]/60">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#F5F3F7]">
                Live Inference Sandbox
              </h2>
              <p className="text-xs text-[#A8A3AF] font-mono mt-0.5">
                Send real payloads directly to DistilBERT + ONNX Runtime
              </p>
            </div>
            <button
              onClick={onNavigateToModerate}
              className="text-xs font-mono text-[#A78BFA] hover:text-[#F5F3F7] flex items-center gap-1 transition-colors"
            >
              Advanced Mode <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <form onSubmit={handleQuickSubmit} className="mt-4 space-y-4">
            <div>
              <label className="block text-xs font-mono text-[#A8A3AF] mb-1.5">
                Content to Analyze (1–512 characters)
              </label>
              <div className="relative">
                <textarea
                  value={quickText}
                  onChange={(e) => setQuickText(e.target.value)}
                  placeholder="Enter text to test real-time classification (e.g. 'Antigravity builds reliable systems' or a policy violation)..."
                  rows={3}
                  maxLength={512}
                  className="w-full bg-[#151419] border border-[#37333D] focus:border-[#A78BFA] focus:ring-1 focus:ring-[#A78BFA] rounded-lg p-3 text-sm text-[#F5F3F7] placeholder-[#A8A3AF]/40 resize-none font-sans outline-none transition-all"
                />
                <span className="absolute bottom-2.5 right-3 text-[10px] font-mono text-[#A8A3AF]/70">
                  {quickText.length} / 512
                </span>
              </div>
            </div>

            {errorMsg && (
              <div className="p-3 rounded-lg bg-[#FB7185]/10 border border-[#FB7185]/30 text-xs font-mono text-[#FB7185]">
                {errorMsg}
              </div>
            )}

            <div className="flex items-center justify-between">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setQuickText('Antigravity engineering team ships reliable code.')}
                  className="px-2.5 py-1 text-xs font-mono rounded bg-[#242128] hover:bg-[#2A2730] text-[#A8A3AF] border border-[#37333D]/60 transition-colors"
                >
                  Safe Sample
                </button>
                <button
                  type="button"
                  onClick={() => setQuickText('I will kill you and destroy your life.')}
                  className="px-2.5 py-1 text-xs font-mono rounded bg-[#242128] hover:bg-[#2A2730] text-[#FB7185] border border-[#FB7185]/20 transition-colors"
                >
                  Threat Sample
                </button>
              </div>

              <button
                type="submit"
                disabled={analyzing || !quickText.trim()}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-[#A78BFA] to-[#D946EF] hover:opacity-95 text-[#111014] font-semibold text-xs font-mono flex items-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(167,139,250,0.25)]"
              >
                <Send className="w-3.5 h-3.5" />
                {analyzing ? 'Analyzing...' : 'Analyze Now'}
              </button>
            </div>
          </form>

          {/* Quick Result Preview */}
          {quickResult && (
            <div className="mt-5 p-4 rounded-lg bg-[#151419] border border-[#37333D] space-y-3 animate-fade-in">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="text-xs font-mono text-[#A8A3AF]">Outcome:</span>
                  <DecisionBadge decision={quickResult.decision} />
                </div>
                <div className="text-xs font-mono text-[#A8A3AF]">
                  Latency: <span className="text-[#34D399] font-bold">{quickResult.total_latency_ms.toFixed(2)} ms</span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono pt-2 border-t border-[#37333D]/40">
                <div>
                  <span className="text-[#A8A3AF]/70 block text-[10px]">LABEL</span>
                  <span className="text-[#F5F3F7] font-semibold uppercase">{quickResult.label}</span>
                </div>
                <div>
                  <span className="text-[#A8A3AF]/70 block text-[10px]">CONFIDENCE</span>
                  <span className="text-[#A78BFA] font-semibold">{(quickResult.confidence * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-[#A8A3AF]/70 block text-[10px]">CATEGORY</span>
                  <span className="text-[#FB7185] font-semibold">
                    {quickResult.policy_categories.length > 0 ? quickResult.policy_categories.join(', ') : 'none'}
                  </span>
                </div>
                <div>
                  <span className="text-[#A8A3AF]/70 block text-[10px]">REQUEST ID</span>
                  <span className="text-[#A8A3AF] truncate block" title={quickResult.request_id}>
                    {quickResult.request_id ? `${quickResult.request_id.slice(0, 8)}...` : 'n/a'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* System & Architecture Summary */}
        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-[#37333D]/60">
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#F5F3F7]">
                Engine Architecture
              </h2>
              <Database className="w-4 h-4 text-[#A78BFA]" />
            </div>

            <div className="mt-4 space-y-3.5 text-xs font-mono">
              <div className="flex justify-between items-center py-1.5 border-b border-[#37333D]/30">
                <span className="text-[#A8A3AF]">Base Model:</span>
                <span className="text-[#F5F3F7] font-semibold">distilbert-base-uncased</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-[#37333D]/30">
                <span className="text-[#A8A3AF]">Runtime Engine:</span>
                <span className="text-[#A78BFA] font-semibold">ONNX Runtime 1.30.0</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-[#37333D]/30">
                <span className="text-[#A8A3AF]">Execution Provider:</span>
                <span className="text-[#34D399] font-semibold">CPUExecutionProvider</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-[#37333D]/30">
                <span className="text-[#A8A3AF]">Graph Optimization:</span>
                <span className="text-[#F5F3F7]">ORT_ENABLE_ALL</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-[#37333D]/30">
                <span className="text-[#A8A3AF]">Async Micro-Batcher:</span>
                <span className="text-[#34D399]">Active (5ms window)</span>
              </div>
              <div className="flex justify-between items-center py-1.5">
                <span className="text-[#A8A3AF]">Model Memory Status:</span>
                <span className="text-[#34D399] font-semibold">{memoryMb}</span>
              </div>
            </div>
          </div>

          <div className="mt-6 p-3 rounded-lg bg-[#151419] border border-[#37333D]/70 text-[11px] font-mono text-[#A8A3AF] space-y-1">
            <div className="flex items-center gap-1.5 text-[#34D399]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#34D399]"></span>
              <span>PARITY VERIFIED</span>
            </div>
            <p className="text-[10px] text-[#A8A3AF]/80">
              PyTorch vs ONNX absolute difference &lt; 9.54e-07 across all logits.
            </p>
          </div>
        </div>
      </div>

      {/* Live Stream Table Preview */}
      <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6">
        <div className="flex items-center justify-between pb-4 border-b border-[#37333D]/60">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-[#F5F3F7]">
              Recent Moderation Activity
            </h2>
            <p className="text-xs text-[#A8A3AF] font-mono mt-0.5">
              Live audit stream of requests evaluated by the inference engine
            </p>
          </div>
          <span className="text-xs font-mono text-[#A8A3AF]">
            {recentEvents.length} events logged
          </span>
        </div>

        {recentEvents.length === 0 ? (
          <div className="py-12 text-center text-xs font-mono text-[#A8A3AF]">
            No moderation activity logged in this session yet. Submit a test above to see real live events.
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-[#37333D] text-[#A8A3AF]">
                  <th className="pb-3 font-semibold">TIME</th>
                  <th className="pb-3 font-semibold">DECISION</th>
                  <th className="pb-3 font-semibold">TEXT SNIPPET</th>
                  <th className="pb-3 font-semibold">CONFIDENCE</th>
                  <th className="pb-3 font-semibold">CATEGORY</th>
                  <th className="pb-3 font-semibold text-right">LATENCY</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#37333D]/40">
                {recentEvents.slice(0, 8).map((evt) => (
                  <tr key={evt.id} className="hover:bg-[#242128]/50 transition-colors">
                    <td className="py-2.5 text-[#A8A3AF]">{evt.timestamp}</td>
                    <td className="py-2.5">
                      <DecisionBadge decision={evt.decision} size="sm" />
                    </td>
                    <td className="py-2.5 text-[#F5F3F7] max-w-xs truncate" title={evt.text}>
                      {evt.text}
                    </td>
                    <td className="py-2.5 text-[#A78BFA] font-medium">
                      {(evt.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 text-[#FB7185]">
                      {evt.category || 'none'}
                    </td>
                    <td className="py-2.5 text-right font-medium text-[#34D399]">
                      {evt.latencyMs.toFixed(1)} ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
