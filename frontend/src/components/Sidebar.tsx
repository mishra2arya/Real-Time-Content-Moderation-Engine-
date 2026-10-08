import React from 'react';
import {
  LayoutDashboard,
  ShieldCheck,
  Activity,
  BarChart3,
  Cpu,
  Terminal,
  Server,
  X,
  Radio,
} from 'lucide-react';

export type PageId = 'dashboard' | 'moderate' | 'stream' | 'analytics' | 'model' | 'api' | 'system';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
  isReady: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  mobileOpen,
  onCloseMobile,
  isReady,
}) => {
  const navItems: { id: PageId; label: string; icon: React.ElementType; badge?: string }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'moderate', label: 'Live Moderation', icon: ShieldCheck },
    { id: 'stream', label: 'Stream Monitor', icon: Radio, badge: 'LIVE' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'model', label: 'Model Specs', icon: Cpu },
    { id: 'api', label: 'API Endpoints', icon: Terminal },
    { id: 'system', label: 'System Health', icon: Server },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-[#111014]/80 backdrop-blur-sm z-40 lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-[#151419] border-r border-[#37333D] flex flex-col transition-transform duration-200 lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header / Brand */}
        <div className="h-16 px-6 border-b border-[#37333D] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#A78BFA] via-[#D946EF] to-[#FB7185] flex items-center justify-center p-0.5 shadow-[0_0_15px_rgba(167,139,250,0.3)]">
              <div className="w-full h-full bg-[#151419] rounded-[7px] flex items-center justify-center">
                <Activity className="w-4 h-4 text-[#A78BFA]" />
              </div>
            </div>
            <div>
              <div className="font-mono font-bold tracking-wider text-sm text-[#F5F3F7] flex items-center gap-1.5">
                AEGIS <span className="text-[#A78BFA] text-xs font-normal">// 1.0</span>
              </div>
              <p className="text-[10px] text-[#A8A3AF] font-mono tracking-tight">AI CONTENT GUARD</p>
            </div>
          </div>

          <button
            onClick={onCloseMobile}
            className="p-1 rounded-md text-[#A8A3AF] hover:text-[#F5F3F7] hover:bg-[#242128] lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* System Status Pill */}
        <div className="px-5 py-4 border-b border-[#37333D]/60 bg-[#19181D]/50">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#A8A3AF] font-medium">Inference Engine</span>
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  isReady ? 'bg-[#34D399] shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse' : 'bg-[#FB7185]'
                }`}
              />
              <span className="text-xs font-mono font-semibold text-[#F5F3F7]">
                {isReady ? 'ONLINE' : 'OFFLINE'}
              </span>
            </div>
          </div>
          <div className="mt-1 text-[11px] font-mono text-[#A8A3AF] truncate">
            DistilBERT + ONNX (CPU-4)
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;

            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectPage(item.id);
                  onCloseMobile();
                }}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-[#1D1B22] text-[#F5F3F7] border border-[#A78BFA]/40 shadow-[0_0_15px_rgba(167,139,250,0.12)]'
                    : 'text-[#A8A3AF] hover:bg-[#1D1B22]/60 hover:text-[#F5F3F7]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={`w-4 h-4 transition-colors ${
                      isActive ? 'text-[#A78BFA]' : 'text-[#A8A3AF] group-hover:text-[#F5F3F7]'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>

                {item.badge && (
                  <span className="px-1.5 py-0.5 text-[9px] font-bold font-mono tracking-wider rounded bg-[#FB7185]/15 text-[#FB7185] border border-[#FB7185]/30 animate-pulse">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer info */}
        <div className="p-4 border-t border-[#37333D] bg-[#111014]/50">
          <div className="flex items-center justify-between text-xs font-mono text-[#A8A3AF]">
            <span>FastAPI + ONNX</span>
            <span className="px-1.5 py-0.5 rounded bg-[#242128] text-[10px] text-[#A78BFA] border border-[#37333D]">
              v1.0.0
            </span>
          </div>
        </div>
      </aside>
    </>
  );
};
