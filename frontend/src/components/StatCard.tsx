import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  icon: LucideIcon;
  accentColor?: 'violet' | 'magenta' | 'emerald' | 'amber' | 'rose';
  loading?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  icon: Icon,
  accentColor = 'violet',
  loading = false,
}) => {
  const accentMap = {
    violet: {
      iconBg: 'bg-[#A78BFA]/10',
      iconText: 'text-[#A78BFA]',
      borderHover: 'hover:border-[#A78BFA]/40',
      glow: 'hover:shadow-[0_0_20px_rgba(167,139,250,0.15)]',
    },
    magenta: {
      iconBg: 'bg-[#D946EF]/10',
      iconText: 'text-[#D946EF]',
      borderHover: 'hover:border-[#D946EF]/40',
      glow: 'hover:shadow-[0_0_20px_rgba(217,70,239,0.15)]',
    },
    emerald: {
      iconBg: 'bg-[#34D399]/10',
      iconText: 'text-[#34D399]',
      borderHover: 'hover:border-[#34D399]/40',
      glow: 'hover:shadow-[0_0_20px_rgba(52,211,153,0.15)]',
    },
    amber: {
      iconBg: 'bg-[#FBBF24]/10',
      iconText: 'text-[#FBBF24]',
      borderHover: 'hover:border-[#FBBF24]/40',
      glow: 'hover:shadow-[0_0_20px_rgba(251,191,36,0.15)]',
    },
    rose: {
      iconBg: 'bg-[#FB7185]/10',
      iconText: 'text-[#FB7185]',
      borderHover: 'hover:border-[#FB7185]/40',
      glow: 'hover:shadow-[0_0_20px_rgba(251,113,133,0.15)]',
    },
  };

  const style = accentMap[accentColor];

  return (
    <div
      className={`bg-[#1D1B22] border border-[#37333D] rounded-xl p-5 transition-all duration-200 ${style.borderHover} ${style.glow}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase font-semibold tracking-wider text-[#A8A3AF]">
          {title}
        </span>
        <div className={`p-2.5 rounded-lg border border-[#37333D]/50 ${style.iconBg} ${style.iconText}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline gap-2">
        {loading ? (
          <div className="h-8 w-24 bg-[#2A2730] animate-pulse rounded"></div>
        ) : (
          <span className="text-2xl font-bold font-mono text-[#F5F3F7] tracking-tight">
            {value}
          </span>
        )}
        {unit && !loading && (
          <span className="text-xs font-mono text-[#A8A3AF] font-medium">{unit}</span>
        )}
      </div>

      {subtitle && (
        <p className="mt-2 text-xs text-[#A8A3AF]/80 flex items-center gap-1 font-mono">
          {subtitle}
        </p>
      )}
    </div>
  );
};
