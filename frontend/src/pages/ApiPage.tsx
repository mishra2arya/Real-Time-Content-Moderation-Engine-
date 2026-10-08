import React, { useState } from 'react';
import { Terminal, Play, CheckCircle2, AlertCircle, Copy, Check } from 'lucide-react';
import { apiClient } from '../api/client';

export const ApiPage: React.FC = () => {
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>('/moderate');
  const [testPayload, setTestPayload] = useState<string>(
    '{\n  "text": "Antigravity provides verified, reliable ML inference pipelines.",\n  "strict": false,\n  "use_batch_queue": false\n}'
  );
  const [isCalling, setIsCalling] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [testStatus, setTestStatus] = useState<number | null>(null);
  const [testLatency, setTestLatency] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);

  const endpoints = [
    {
      method: 'GET',
      path: '/health',
      description: 'Liveness probe returning application operational status',
      samplePayload: null,
      auth: 'None',
    },
    {
      method: 'GET',
      path: '/ready',
      description: 'Readiness probe verifying ONNX model load & system telemetry',
      samplePayload: null,
      auth: 'None',
    },
    {
      method: 'GET',
      path: '/version',
      description: 'Engine, model, and runtime metadata exposition',
      samplePayload: null,
      auth: 'None',
    },
    {
      method: 'POST',
      path: '/moderate',
      description: 'Real-time single-item moderation with category violation tagging',
      samplePayload: '{\n  "text": "Antigravity provides verified, reliable ML inference pipelines.",\n  "strict": false,\n  "use_batch_queue": false\n}',
      auth: 'Optional API Key',
    },
    {
      method: 'POST',
      path: '/moderate/batch',
      description: 'Vectorized batch moderation with single tensor forward pass',
      samplePayload: '{\n  "items": [\n    {"text": "Have a wonderful weekend ahead!"},\n    {"text": "You are completely useless."}\n  ],\n  "strict": false\n}',
      auth: 'Optional API Key',
    },
    {
      method: 'GET',
      path: '/metrics',
      description: 'Prometheus format metrics exposition for Grafana/monitoring',
      samplePayload: null,
      auth: 'None',
    },
  ];

  const handleSelectEndpoint = (path: string, payload: string | null) => {
    setSelectedEndpoint(path);
    if (payload !== null) {
      setTestPayload(payload);
    }
    setTestResult(null);
    setTestStatus(null);
    setTestLatency(null);
  };

  const handleExecute = async () => {
    setIsCalling(true);
    setTestResult(null);
    setTestStatus(null);
    const start = performance.now();

    try {
      if (selectedEndpoint === '/health') {
        const res = await apiClient.getHealth();
        setTestResult(JSON.stringify(res, null, 2));
        setTestStatus(200);
      } else if (selectedEndpoint === '/ready') {
        const res = await apiClient.getReadiness();
        setTestResult(JSON.stringify(res, null, 2));
        setTestStatus(200);
      } else if (selectedEndpoint === '/version') {
        const res = await apiClient.getVersion();
        setTestResult(JSON.stringify(res, null, 2));
        setTestStatus(200);
      } else if (selectedEndpoint === '/moderate') {
        const parsed = JSON.parse(testPayload);
        const res = await apiClient.moderateText(parsed);
        setTestResult(JSON.stringify(res, null, 2));
        setTestStatus(200);
      } else if (selectedEndpoint === '/moderate/batch') {
        const parsed = JSON.parse(testPayload);
        const res = await apiClient.moderateBatch(parsed);
        setTestResult(JSON.stringify(res, null, 2));
        setTestStatus(200);
      } else if (selectedEndpoint === '/metrics') {
        const res = await apiClient.getRawMetrics();
        setTestResult(res.slice(0, 1200) + '\n... (truncated for display)');
        setTestStatus(200);
      }
    } catch (err: unknown) {
      setTestResult(err instanceof Error ? err.message : 'Unknown error occurred');
      setTestStatus(500);
    } finally {
      setTestLatency(Math.round(performance.now() - start));
      setIsCalling(false);
    }
  };

  const copyResult = () => {
    if (!testResult) return;
    navigator.clipboard.writeText(testResult);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-xl bg-[#1D1B22] border border-[#37333D] flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-[#F5F3F7] flex items-center gap-2">
            <Terminal className="w-4 h-4 text-[#A78BFA]" />
            FastAPI Endpoint Reference & Live Query Runner
          </h2>
          <p className="text-xs text-[#A8A3AF] font-mono mt-0.5">
            Test and inspect all 6 production endpoints directly against the running microservice
          </p>
        </div>
      </div>

      {/* Main Grid: Endpoints List + Live Runner */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Endpoints Directory */}
        <div className="lg:col-span-5 space-y-3">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#A8A3AF] px-1">
            Registered REST Endpoints
          </h3>

          <div className="space-y-2">
            {endpoints.map((ep) => {
              const isSelected = selectedEndpoint === ep.path;
              return (
                <div
                  key={ep.path}
                  onClick={() => handleSelectEndpoint(ep.path, ep.samplePayload)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all duration-150 ${
                    isSelected
                      ? 'bg-[#1D1B22] border-[#A78BFA]/50 shadow-[0_0_15px_rgba(167,139,250,0.12)]'
                      : 'bg-[#151419] border-[#37333D] hover:bg-[#1D1B22]/80 hover:border-[#37333D]/80'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          ep.method === 'GET'
                            ? 'bg-[#34D399]/15 text-[#34D399] border border-[#34D399]/30'
                            : 'bg-[#A78BFA]/15 text-[#A78BFA] border border-[#A78BFA]/30'
                        }`}
                      >
                        {ep.method}
                      </span>
                      <span className="text-xs font-mono font-bold text-[#F5F3F7]">
                        {ep.path}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-[#A8A3AF]/70">
                      {ep.auth}
                    </span>
                  </div>

                  <p className="text-[11px] text-[#A8A3AF] font-sans mt-2">
                    {ep.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Query Console */}
        <div className="lg:col-span-7 bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#37333D]/60">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-[#A78BFA]">REQUEST TESTER:</span>
                <span className="text-xs font-mono font-semibold text-[#F5F3F7]">{selectedEndpoint}</span>
              </div>

              {testStatus && (
                <div className="flex items-center gap-2 text-xs font-mono">
                  <span
                    className={`flex items-center gap-1 font-bold ${
                      testStatus === 200 ? 'text-[#34D399]' : 'text-[#FB7185]'
                    }`}
                  >
                    {testStatus === 200 ? (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    ) : (
                      <AlertCircle className="w-3.5 h-3.5" />
                    )}
                    {testStatus} OK
                  </span>
                  {testLatency && (
                    <span className="text-[#A8A3AF]">({testLatency}ms)</span>
                  )}
                </div>
              )}
            </div>

            {/* Request Body Area (if POST) */}
            {selectedEndpoint.startsWith('/moderate') && (
              <div className="mt-4">
                <label className="block text-xs font-mono text-[#A8A3AF] mb-1.5">
                  JSON Request Body
                </label>
                <textarea
                  value={testPayload}
                  onChange={(e) => setTestPayload(e.target.value)}
                  rows={5}
                  className="w-full bg-[#151419] border border-[#37333D] focus:border-[#A78BFA] focus:ring-1 focus:ring-[#A78BFA] rounded-lg p-3 text-xs font-mono text-[#F5F3F7] placeholder-[#A8A3AF]/40 resize-y outline-none transition-all"
                />
              </div>
            )}

            {/* Execute Button */}
            <div className="flex justify-end mt-4">
              <button
                onClick={handleExecute}
                disabled={isCalling}
                className="px-5 py-2 rounded-lg bg-gradient-to-r from-[#A78BFA] to-[#D946EF] hover:opacity-95 text-[#111014] font-semibold text-xs font-mono flex items-center gap-2 transition-all disabled:opacity-40 shadow-[0_0_15px_rgba(167,139,250,0.25)]"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                {isCalling ? 'Sending Request...' : 'Send Live Request'}
              </button>
            </div>

            {/* Response Output Box */}
            <div className="mt-5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#A8A3AF]">LIVE HTTP RESPONSE BODY</span>
                {testResult && (
                  <button
                    onClick={copyResult}
                    className="flex items-center gap-1 text-[11px] font-mono text-[#A78BFA] hover:text-[#F5F3F7] transition-colors"
                  >
                    {copied ? <Check className="w-3 h-3 text-[#34D399]" /> : <Copy className="w-3 h-3" />}
                    <span>{copied ? 'Copied' : 'Copy'}</span>
                  </button>
                )}
              </div>

              <div className="p-4 rounded-xl bg-[#151419] border border-[#37333D] font-mono text-xs max-h-80 overflow-y-auto">
                {testResult ? (
                  <pre className="text-[#F5F3F7] whitespace-pre-wrap">{testResult}</pre>
                ) : (
                  <span className="text-[#A8A3AF]/50 italic">
                    Click "Send Live Request" above to execute real HTTP roundtrip.
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
