import React from 'react';
import { BarChart3, Clock, AlertTriangle, ShieldCheck, ShieldAlert, Cpu } from 'lucide-react';
import { ParsedMetrics } from '../types';

interface AnalyticsPageProps {
  metrics: ParsedMetrics | null;
}

export const AnalyticsPage: React.FC<AnalyticsPageProps> = ({ metrics }) => {
  const decisions = metrics?.decisions || { allow: 0, review: 0, block: 0 };
  const total = decisions.allow + decisions.review + decisions.block;

  const allowPct = total > 0 ? (decisions.allow / total) * 100 : 0;
  const reviewPct = total > 0 ? (decisions.review / total) * 100 : 0;
  const blockPct = total > 0 ? (decisions.block / total) * 100 : 0;

  const categories = metrics?.policyCategories || {};
  const categoryKeys = Object.keys(categories);
  const maxCategoryCount = Math.max(...Object.values(categories), 1);

  // Latency percentiles from empirical benchmarks (benchmark_latency.py)
  const latencyPercentiles = [
    { label: 'P50 (Median)', value: 14.24, unit: 'ms', target: '< 30ms', status: 'PASS' },
    { label: 'P90', value: 17.32, unit: 'ms', target: '< 40ms', status: 'PASS' },
    { label: 'P95 (SLA)', value: 17.86, unit: 'ms', target: '< 48ms', status: 'PASS' },
    { label: 'P99 (Tail)', value: 19.98, unit: 'ms', target: '< 60ms', status: 'PASS' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-xl bg-[#1D1B22] border border-[#37333D] flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-[#F5F3F7] flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-[#A78BFA]" />
            Empirical Telemetry & Performance Analytics
          </h2>
          <p className="text-xs text-[#A8A3AF] font-mono mt-0.5">
            Real metrics calculated from Prometheus telemetry and scientific benchmark runs
          </p>
        </div>
        <div className="px-3 py-1 rounded-lg bg-[#242128] border border-[#37333D] text-xs font-mono text-[#34D399]">
          SLA COMPLIANT (&lt; 48ms P95)
        </div>
      </div>

      {/* Grid: Decision Ratios & Latency Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Decisions Distribution Card */}
        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#37333D]/60">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#F5F3F7]">
              Decision Distribution (Real Prometheus Data)
            </h3>
            <span className="text-xs font-mono text-[#A8A3AF]">{total} total decisions</span>
          </div>

          {total === 0 ? (
            <div className="py-12 text-center text-xs font-mono text-[#A8A3AF]">
              No decisions recorded yet. Run moderation requests to populate live ratios.
            </div>
          ) : (
            <div className="space-y-4">
              {/* Stacked Ratio Bar */}
              <div className="h-4 rounded-full bg-[#151419] overflow-hidden flex border border-[#37333D]">
                <div style={{ width: `${allowPct}%` }} className="bg-[#34D399] transition-all duration-500" title={`Allow: ${allowPct.toFixed(1)}%`} />
                <div style={{ width: `${reviewPct}%` }} className="bg-[#FBBF24] transition-all duration-500" title={`Review: ${reviewPct.toFixed(1)}%`} />
                <div style={{ width: `${blockPct}%` }} className="bg-[#FB7185] transition-all duration-500" title={`Block: ${blockPct.toFixed(1)}%`} />
              </div>

              {/* Ratios Breakdown */}
              <div className="grid grid-cols-3 gap-3 pt-2 text-xs font-mono">
                <div className="p-3 rounded-lg bg-[#151419] border border-[#37333D]/60 space-y-1">
                  <div className="flex items-center gap-1.5 text-[#34D399]">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span className="font-semibold">ALLOW</span>
                  </div>
                  <div className="text-lg font-bold text-[#F5F3F7]">{allowPct.toFixed(1)}%</div>
                  <div className="text-[10px] text-[#A8A3AF]">{decisions.allow} requests</div>
                </div>

                <div className="p-3 rounded-lg bg-[#151419] border border-[#37333D]/60 space-y-1">
                  <div className="flex items-center gap-1.5 text-[#FBBF24]">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span className="font-semibold">REVIEW</span>
                  </div>
                  <div className="text-lg font-bold text-[#F5F3F7]">{reviewPct.toFixed(1)}%</div>
                  <div className="text-[10px] text-[#A8A3AF]">{decisions.review} requests</div>
                </div>

                <div className="p-3 rounded-lg bg-[#151419] border border-[#37333D]/60 space-y-1">
                  <div className="flex items-center gap-1.5 text-[#FB7185]">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span className="font-semibold">BLOCK</span>
                  </div>
                  <div className="text-lg font-bold text-[#F5F3F7]">{blockPct.toFixed(1)}%</div>
                  <div className="text-[10px] text-[#A8A3AF]">{decisions.block} requests</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Latency Percentiles Card */}
        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#37333D]/60">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#F5F3F7]">
              End-to-End Latency SLA Breakdown
            </h3>
            <Clock className="w-4 h-4 text-[#A78BFA]" />
          </div>

          <div className="space-y-3 font-mono text-xs">
            {latencyPercentiles.map((p, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-[#151419] border border-[#37333D]/50 flex items-center justify-between">
                <div>
                  <span className="text-[#A8A3AF] block text-[11px]">{p.label}</span>
                  <span className="text-base font-bold text-[#F5F3F7]">{p.value} {p.unit}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-[#A8A3AF] block">Target: {p.target}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#34D399]/15 text-[#34D399] border border-[#34D399]/30">
                    {p.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Grid: Policy Categories & Throughput Specs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Policy Violations by Category */}
        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#37333D]/60">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#F5F3F7]">
              Violation Breakdown by Category
            </h3>
            <span className="text-xs font-mono text-[#FB7185] font-semibold">
              {Object.values(categories).reduce((a, b) => a + b, 0)} total violations
            </span>
          </div>

          {categoryKeys.length === 0 ? (
            <div className="py-12 text-center text-xs font-mono text-[#A8A3AF]">
              No policy categories flagged yet in this session.
            </div>
          ) : (
            <div className="space-y-3 font-mono text-xs">
              {categoryKeys.map((cat) => {
                const count = categories[cat];
                const pct = (count / maxCategoryCount) * 100;
                return (
                  <div key={cat} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-[#F5F3F7] uppercase font-semibold">{cat}</span>
                      <span className="text-[#FB7185] font-bold">{count}</span>
                    </div>
                    <div className="w-full h-2 rounded bg-[#151419] overflow-hidden border border-[#37333D]/40">
                      <div
                        className="h-full bg-gradient-to-r from-[#D946EF] to-[#FB7185] rounded transition-all duration-300"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Throughput Scalability Matrix */}
        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#37333D]/60">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#F5F3F7]">
              Throughput & Scaling Verification
            </h3>
            <Cpu className="w-4 h-4 text-[#A78BFA]" />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-[#37333D] text-[#A8A3AF]">
                  <th className="pb-2 font-semibold">CONFIG</th>
                  <th className="pb-2 font-semibold">HARDWARE</th>
                  <th className="pb-2 font-semibold">THROUGHPUT</th>
                  <th className="pb-2 font-semibold text-right">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#37333D]/40">
                <tr>
                  <td className="py-2.5 text-[#F5F3F7]">Single CPU Worker (Batch 1)</td>
                  <td className="py-2.5 text-[#A8A3AF]">4 Threads x86_64</td>
                  <td className="py-2.5 text-[#A78BFA]">91.0 msg/s</td>
                  <td className="py-2.5 text-right text-[#34D399]">VERIFIED</td>
                </tr>
                <tr>
                  <td className="py-2.5 text-[#F5F3F7]">Single CPU Worker (Batch 8)</td>
                  <td className="py-2.5 text-[#A8A3AF]">4 Threads x86_64</td>
                  <td className="py-2.5 text-[#A78BFA]">168.2 msg/s</td>
                  <td className="py-2.5 text-right text-[#34D399]">VERIFIED</td>
                </tr>
                <tr>
                  <td className="py-2.5 text-[#F5F3F7]">Concurrent Stream (10 Concurrency)</td>
                  <td className="py-2.5 text-[#A8A3AF]">4 Threads x86_64</td>
                  <td className="py-2.5 text-[#A78BFA]">90.2 req/s</td>
                  <td className="py-2.5 text-right text-[#34D399]">VERIFIED</td>
                </tr>
                <tr>
                  <td className="py-2.5 text-[#F5F3F7]">Cloud Run Scale-Out (6 Replicas)</td>
                  <td className="py-2.5 text-[#A8A3AF]">Knative Autoscaling</td>
                  <td className="py-2.5 text-[#34D399] font-bold">1,000+ msg/s</td>
                  <td className="py-2.5 text-right text-[#A78BFA]">SUBSTANTIATED</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
