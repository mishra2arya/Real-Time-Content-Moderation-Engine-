import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar, PageId } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { LiveModerationPage } from './pages/LiveModerationPage';
import { StreamMonitorPage } from './pages/StreamMonitorPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ModelPage } from './pages/ModelPage';
import { ApiPage } from './pages/ApiPage';
import { SystemPage } from './pages/SystemPage';
import {
  HealthResponse,
  ReadinessResponse,
  VersionResponse,
  ParsedMetrics,
  ModerationEvent,
} from './types';
import { apiClient } from './api/client';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [mobileOpen, setMobileOpen] = useState(false);

  // Core API states
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [version, setVersion] = useState<VersionResponse | null>(null);
  const [metrics, setMetrics] = useState<ParsedMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Live session events
  const [recentEvents, setRecentEvents] = useState<ModerationEvent[]>([]);

  const fetchTelemetry = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [h, r, v, m] = await Promise.allSettled([
        apiClient.getHealth(),
        apiClient.getReadiness(),
        apiClient.getVersion(),
        apiClient.getParsedMetrics(),
      ]);

      if (h.status === 'fulfilled') setHealth(h.value);
      if (r.status === 'fulfilled') setReadiness(r.value);
      if (v.status === 'fulfilled') setVersion(v.value);
      if (m.status === 'fulfilled') setMetrics(m.value);
    } catch {
      // ignore
    } finally {
      setIsRefreshing(false);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 10000); // 10s telemetry polling
    return () => clearInterval(interval);
  }, [fetchTelemetry]);

  const handleNewEvent = (event: ModerationEvent) => {
    setRecentEvents((prev) => [event, ...prev].slice(0, 50));
    fetchTelemetry(); // update metric counters immediately
  };

  const handleClearEvents = () => {
    setRecentEvents([]);
  };

  const pageMeta: Record<PageId, { title: string; subtitle: string }> = {
    dashboard: {
      title: 'Operations Dashboard',
      subtitle: 'Real-time overview of content moderation pipeline and metrics',
    },
    moderate: {
      title: 'Live Moderation Console',
      subtitle: 'Interactive single-item and vectorized batch classification',
    },
    stream: {
      title: 'Event Stream Monitor',
      subtitle: 'Continuous real-time audit feed of evaluated content',
    },
    analytics: {
      title: 'Telemetry & Analytics',
      subtitle: 'Empirical latency distribution and policy violation analysis',
    },
    model: {
      title: 'Model Specifications',
      subtitle: 'DistilBERT parameters, ONNX optimizations, and evaluation results',
    },
    api: {
      title: 'API Reference & Tester',
      subtitle: 'FastAPI interactive REST interface and live request executor',
    },
    system: {
      title: 'System Infrastructure',
      subtitle: 'Operating system metrics, memory RSS, and Cloud Run specs',
    },
  };

  return (
    <div className="min-h-screen bg-[#111014] text-[#F5F3F7] flex flex-col lg:flex-row font-sans">
      {/* Sidebar navigation */}
      <Sidebar
        currentPage={currentPage}
        onSelectPage={setCurrentPage}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
        isReady={readiness?.model_ready ?? false}
      />

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        <Header
          title={pageMeta[currentPage].title}
          subtitle={pageMeta[currentPage].subtitle}
          onOpenMobile={() => setMobileOpen(true)}
          onRefresh={fetchTelemetry}
          isRefreshing={isRefreshing}
          isReady={readiness?.model_ready ?? false}
        />

        <main className="flex-1 p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {currentPage === 'dashboard' && (
            <DashboardPage
              metrics={metrics}
              readiness={readiness}
              recentEvents={recentEvents}
              onNewEvent={handleNewEvent}
              loading={loading}
              onNavigateToModerate={() => setCurrentPage('moderate')}
            />
          )}

          {currentPage === 'moderate' && (
            <LiveModerationPage onNewEvent={handleNewEvent} />
          )}

          {currentPage === 'stream' && (
            <StreamMonitorPage
              events={recentEvents}
              onClearEvents={handleClearEvents}
            />
          )}

          {currentPage === 'analytics' && (
            <AnalyticsPage metrics={metrics} />
          )}

          {currentPage === 'model' && (
            <ModelPage readiness={readiness} version={version} />
          )}

          {currentPage === 'api' && <ApiPage />}

          {currentPage === 'system' && (
            <SystemPage
              health={health}
              readiness={readiness}
              version={version}
              onRefresh={fetchTelemetry}
              isRefreshing={isRefreshing}
            />
          )}
        </main>
      </div>
    </div>
  );
};
