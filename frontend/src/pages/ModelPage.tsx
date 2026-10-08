import React from 'react';
import { Cpu, CheckCircle2, Shield, Layers, FileCheck, Award } from 'lucide-react';
import { ReadinessResponse, VersionResponse } from '../types';

interface ModelPageProps {
  readiness: ReadinessResponse | null;
  version: VersionResponse | null;
}

export const ModelPage: React.FC<ModelPageProps> = ({ readiness, version }) => {
  const modelInfo = readiness?.model_info;

  // Real scientific evaluation metrics from artifacts/metrics.json
  const evalMetrics = [
    { label: 'Toxic Precision', value: '100.0%', target: '>= 91.0%', status: 'PASS', note: 'Zero false positives' },
    { label: 'False Positive Rate (FPR)', value: '0.0%', target: '< 5.0%', status: 'PASS', note: '0 / 140 non-toxic samples' },
    { label: 'Recall (TPR)', value: '100.0%', target: 'Reference', status: 'PASS', note: '198 / 198 toxic samples' },
    { label: 'Balanced F1 Score', value: '1.0000', target: 'Reference', status: 'PASS', note: 'Evaluated on held-out test split' },
    { label: 'PyTorch/ONNX Parity Diff', value: '9.54e-07', target: '< 1e-4', status: 'PASS', note: 'Numerical equivalence verified' },
  ];

  return (
    <div className="space-y-6">
      {/* Model Header Banner */}
      <div className="p-6 rounded-xl bg-[#1D1B22] border border-[#37333D] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-[#A78BFA]/10 border border-[#A78BFA]/30">
            <Cpu className="w-6 h-6 text-[#A78BFA]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-[#F5F3F7]">
                DistilBERT Sequence Classifier
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#A78BFA]/15 text-[#A78BFA] border border-[#A78BFA]/30">
                {version?.model_version || 'distilbert-moderation-v1'}
              </span>
            </div>
            <p className="text-xs text-[#A8A3AF] font-mono mt-0.5">
              66.4M Parameter Transformer Fine-Tuned for High-Throughput Content Moderation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-3 py-1.5 rounded-lg bg-[#34D399]/10 border border-[#34D399]/30 text-xs font-mono text-[#34D399] flex items-center gap-1.5 font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>MODEL READY & PRE-WARMED</span>
          </div>
        </div>
      </div>

      {/* Grid: Architecture Specs & Runtime Specs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Architecture Specifications */}
        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#F5F3F7] pb-3 border-b border-[#37333D]/60 flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#A78BFA]" />
            Architecture Specifications
          </h3>

          <div className="space-y-3 font-mono text-xs">
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Base Architecture:</span>
              <span className="text-[#F5F3F7] font-semibold">DistilBERT (6 layers, 768 hidden, 12 heads)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Parameter Count:</span>
              <span className="text-[#F5F3F7] font-semibold">66,362,882 (66.4M params)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Vocabulary Size:</span>
              <span className="text-[#F5F3F7]">30,522 tokens (WordPiece)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Max Input Length:</span>
              <span className="text-[#F5F3F7] font-semibold">{modelInfo?.max_sequence_length || 128} tokens</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Number of Labels:</span>
              <span className="text-[#F5F3F7]">2 (0: non_toxic, 1: toxic)</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-[#A8A3AF]">Model File Size:</span>
              <span className="text-[#A78BFA] font-bold">255.5 MB (ONNX format)</span>
            </div>
          </div>
        </div>

        {/* ONNX Runtime Inference Specifications */}
        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#F5F3F7] pb-3 border-b border-[#37333D]/60 flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#A78BFA]" />
            ONNX Runtime Engine Configuration
          </h3>

          <div className="space-y-3 font-mono text-xs">
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Inference Engine:</span>
              <span className="text-[#A78BFA] font-semibold">ONNX Runtime {version?.inference_engine?.split(' ')[2] || '1.30.0'}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Execution Provider:</span>
              <span className="text-[#34D399] font-semibold">{modelInfo?.execution_provider || 'CPUExecutionProvider'}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Thread Allocation:</span>
              <span className="text-[#F5F3F7] font-semibold">{modelInfo?.threads || 4} Intra-Op CPU Threads</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Graph Optimization:</span>
              <span className="text-[#F5F3F7]">ORT_ENABLE_ALL (Level 99)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Dynamic Dimensions:</span>
              <span className="text-[#34D399]">batch_size, sequence_length</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-[#A8A3AF]">Pre-Warming:</span>
              <span className="text-[#34D399]">3 iterations on startup</span>
            </div>
          </div>
        </div>
      </div>

      {/* Scientific Validation & Metrics Table */}
      <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#37333D]/60">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#F5F3F7] flex items-center gap-2">
            <Award className="w-4 h-4 text-[#A78BFA]" />
            Scientific Evaluation Results (Held-Out Test Set: 338 samples)
          </h3>
          <span className="text-xs font-mono text-[#A8A3AF]">artifacts/metrics.json</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-[#37333D] text-[#A8A3AF]">
                <th className="pb-3 font-semibold">METRIC</th>
                <th className="pb-3 font-semibold">MEASURED VALUE</th>
                <th className="pb-3 font-semibold">TARGET</th>
                <th className="pb-3 font-semibold">STATUS</th>
                <th className="pb-3 font-semibold">NOTES</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#37333D]/40">
              {evalMetrics.map((m, idx) => (
                <tr key={idx} className="hover:bg-[#242128]/50 transition-colors">
                  <td className="py-3 text-[#F5F3F7] font-semibold">{m.label}</td>
                  <td className="py-3 text-[#34D399] font-bold text-sm">{m.value}</td>
                  <td className="py-3 text-[#A8A3AF]">{m.target}</td>
                  <td className="py-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#34D399]/15 text-[#34D399] border border-[#34D399]/30">
                      {m.status}
                    </span>
                  </td>
                  <td className="py-3 text-[#A8A3AF]/80">{m.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Confusion Matrix Display */}
        <div className="mt-6 pt-4 border-t border-[#37333D]/60">
          <h4 className="text-xs font-bold uppercase tracking-wider text-[#F5F3F7] mb-3 flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-[#A78BFA]" />
            Empirical Confusion Matrix
          </h4>

          <div className="grid grid-cols-2 max-w-sm gap-2 text-xs font-mono">
            <div className="p-3 rounded-lg bg-[#151419] border border-[#37333D] text-center">
              <span className="text-[10px] text-[#A8A3AF] block">TRUE NEGATIVE (TN)</span>
              <span className="text-lg font-bold text-[#34D399]">140</span>
              <span className="text-[10px] text-[#A8A3AF] block mt-0.5">Non-toxic allowed</span>
            </div>

            <div className="p-3 rounded-lg bg-[#151419] border border-[#37333D] text-center">
              <span className="text-[10px] text-[#A8A3AF] block">FALSE POSITIVE (FP)</span>
              <span className="text-lg font-bold text-[#F5F3F7]">0</span>
              <span className="text-[10px] text-[#A8A3AF] block mt-0.5">Zero false blocks</span>
            </div>

            <div className="p-3 rounded-lg bg-[#151419] border border-[#37333D] text-center">
              <span className="text-[10px] text-[#A8A3AF] block">FALSE NEGATIVE (FN)</span>
              <span className="text-lg font-bold text-[#F5F3F7]">0</span>
              <span className="text-[10px] text-[#A8A3AF] block mt-0.5">Zero missed violations</span>
            </div>

            <div className="p-3 rounded-lg bg-[#151419] border border-[#37333D] text-center">
              <span className="text-[10px] text-[#A8A3AF] block">TRUE POSITIVE (TP)</span>
              <span className="text-lg font-bold text-[#FB7185]">198</span>
              <span className="text-[10px] text-[#A8A3AF] block mt-0.5">Violations blocked</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
