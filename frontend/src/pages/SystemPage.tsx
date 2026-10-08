import React, { useState } from 'react';
import { Server, Activity, ShieldCheck, RefreshCw, FileText } from 'lucide-react';
import { ReadinessResponse, HealthResponse, VersionResponse } from '../types';
import { apiClient } from '../api/client';

interface SystemPageProps {
  health: HealthResponse | null;
  readiness: ReadinessResponse | null;
  version: VersionResponse | null;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const SystemPage: React.FC<SystemPageProps> = ({
  health,
  readiness,
  version,
  onRefresh,
  isRefreshing,
}) => {
  const [rawMetrics, setRawMetrics] = useState<string | null>(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  const sys = readiness?.system;

  const handleFetchMetrics = async () => {
    setLoadingMetrics(true);
    try {
      const text = await apiClient.getRawMetrics();
      setRawMetrics(text);
    } catch {
      setRawMetrics('Failed to fetch Prometheus metrics.');
    } finally {
      setLoadingMetrics(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-xl bg-[#1D1B22] border border-[#37333D] flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-[#34D399]/10 border border-[#34D399]/30">
            <Server className="w-5 h-5 text-[#34D399]" />
          </div>
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-[#F5F3F7]">
              Infrastructure & Process Telemetry
            </h2>
            <p className="text-xs text-[#A8A3AF] font-mono mt-0.5">
              Live operating system metrics gathered via psutil and FastAPI probes
            </p>
          </div>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-[#37333D] bg-[#151419] hover:bg-[#242128] text-xs font-mono text-[#F5F3F7] transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-[#A78BFA] ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Probes</span>
        </button>
      </div>

      {/* Primary Telemetry Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-4">
          <span className="text-[10px] text-[#A8A3AF] uppercase block">PROCESS MEMORY (RSS)</span>
          <span className="text-xl font-bold text-[#34D399] mt-1 block">
            {sys?.memory_rss_mb ? `${sys.memory_rss_mb} MB` : 'No data'}
          </span>
          <span className="text-[10px] text-[#A8A3AF]/70 block mt-1">Single worker resident</span>
        </div>

        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-4">
          <span className="text-[10px] text-[#A8A3AF] uppercase block">ACTIVE THREADS</span>
          <span className="text-xl font-bold text-[#A78BFA] mt-1 block">
            {sys?.num_threads ?? 'No data'}
          </span>
          <span className="text-[10px] text-[#A8A3AF]/70 block mt-1">Including ONNX intra-op pool</span>
        </div>

        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-4">
          <span className="text-[10px] text-[#A8A3AF] uppercase block">CPU UTILIZATION</span>
          <span className="text-xl font-bold text-[#F5F3F7] mt-1 block">
            {sys?.cpu_percent !== undefined ? `${sys.cpu_percent}%` : '0.0%'}
          </span>
          <span className="text-[10px] text-[#A8A3AF]/70 block mt-1">Instantaneous process load</span>
        </div>

        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-4">
          <span className="text-[10px] text-[#A8A3AF] uppercase block">LIVENESS STATUS</span>
          <span className="text-xl font-bold text-[#34D399] mt-1 block">
            {health?.status ? health.status.toUpperCase() : 'OFFLINE'}
          </span>
          <span className="text-[10px] text-[#A8A3AF]/70 block mt-1">HTTP 200 via /health</span>
        </div>
      </div>

      {/* Configuration & Scalability Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Runtime Environment */}
        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-4 font-mono text-xs">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#F5F3F7] pb-3 border-b border-[#37333D]/60 flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#A78BFA]" />
            Runtime Environment
          </h3>

          <div className="space-y-3">
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Python Version:</span>
              <span className="text-[#F5F3F7]">{version?.python_version || '3.13.12'}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">FastAPI Application:</span>
              <span className="text-[#F5F3F7]">{health?.app_name || 'Real-Time Content Moderation Engine'}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Application Environment:</span>
              <span className="text-[#34D399] uppercase font-bold">{health?.environment || 'production'}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Host Operating System:</span>
              <span className="text-[#F5F3F7]">Linux x86_64</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-[#A8A3AF]">Container State:</span>
              <span className="text-[#34D399]">Non-root UID 10001 (appuser)</span>
            </div>
          </div>
        </div>

        {/* Cloud Run Autoscaling Profile */}
        <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-4 font-mono text-xs">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#F5F3F7] pb-3 border-b border-[#37333D]/60 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#A78BFA]" />
            GCP Cloud Run Scalability Profile (service.yaml)
          </h3>

          <div className="space-y-3">
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Min / Max Scale:</span>
              <span className="text-[#34D399] font-bold">1 min / 20 max instances</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Instance Concurrency:</span>
              <span className="text-[#F5F3F7]">80 concurrent connections</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Resource Allocation:</span>
              <span className="text-[#F5F3F7]">2.0 vCPU, 2 GiB RAM per replica</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#37333D]/30">
              <span className="text-[#A8A3AF]">Startup CPU Boost:</span>
              <span className="text-[#34D399]">Enabled (run.googleapis.com)</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-[#A8A3AF]">Maximum System Concurrency:</span>
              <span className="text-[#A78BFA] font-bold">1,600 concurrent requests</span>
            </div>
          </div>
        </div>
      </div>

      {/* Raw Prometheus Telemetry Inspector */}
      <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#37333D]/60">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-[#A78BFA]" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#F5F3F7]">
              Raw Prometheus Metric Feed
            </h3>
          </div>
          <button
            onClick={handleFetchMetrics}
            disabled={loadingMetrics}
            className="px-3 py-1 rounded bg-[#151419] hover:bg-[#242128] border border-[#37333D] text-xs font-mono text-[#A78BFA] transition-colors"
          >
            {loadingMetrics ? 'Fetching...' : rawMetrics ? 'Reload Stream' : 'Load Stream'}
          </button>
        </div>

        {rawMetrics && (
          <div className="p-4 rounded-xl bg-[#151419] border border-[#37333D] font-mono text-xs max-h-72 overflow-y-auto">
            <pre className="text-[#A8A3AF]">{rawMetrics}</pre>
          </div>
        )}
      </div>
    </div>
  );
};
