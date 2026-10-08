import React from 'react';
import { Menu, RefreshCw, Shield, Clock } from 'lucide-react';

interface HeaderProps {
  title: string;
  subtitle: string;
  onOpenMobile: () => void;
  onRefresh: () => void;
  isRefreshing: boolean;
  isReady: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  onOpenMobile,
  onRefresh,
  isRefreshing,
  isReady,
}) => {
  return (
    <header className="h-16 px-6 lg:px-8 border-b border-[#37333D] bg-[#151419]/90 backdrop-blur-md sticky top-0 z-30 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <button
          onClick={onOpenMobile}
          className="p-2 rounded-lg text-[#A8A3AF] hover:text-[#F5F3F7] hover:bg-[#242128] lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <h1 className="text-base font-bold text-[#F5F3F7] tracking-tight">{title}</h1>
          <p className="text-xs text-[#A8A3AF] font-mono">{subtitle}</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Backend health status pill */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#37333D] bg-[#1D1B22] text-xs font-mono">
          <Shield className="w-3.5 h-3.5 text-[#A78BFA]" />
          <span className="text-[#A8A3AF]">STATUS:</span>
          <span className={`font-semibold ${isReady ? 'text-[#34D399]' : 'text-[#FB7185]'}`}>
            {isReady ? '200 OK' : 'OFFLINE'}
          </span>
        </div>

        {/* Refresh button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh metrics & status"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#37333D] bg-[#1D1B22] hover:bg-[#242128] hover:border-[#A78BFA]/50 text-[#F5F3F7] text-xs font-mono transition-all duration-150"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-[#A78BFA] ${isRefreshing ? 'animate-spin' : ''}`} />
          <span className="hidden md:inline">Sync Metrics</span>
        </button>

        {/* Real-time timestamp */}
        <div className="hidden lg:flex items-center gap-1.5 text-xs font-mono text-[#A8A3AF] px-2.5 py-1 rounded bg-[#111014] border border-[#37333D]/50">
          <Clock className="w-3.5 h-3.5 text-[#A78BFA]" />
          <span>UTC</span>
        </div>
      </div>
    </header>
  );
};
