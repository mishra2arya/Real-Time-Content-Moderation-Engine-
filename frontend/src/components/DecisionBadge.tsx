import React from 'react';
import { ModerationDecision } from '../types';
import { CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';

interface DecisionBadgeProps {
  decision: ModerationDecision;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const DecisionBadge: React.FC<DecisionBadgeProps> = ({
  decision,
  size = 'md',
  showIcon = true,
}) => {
  const configs = {
    allow: {
      label: 'ALLOW',
      icon: CheckCircle2,
      bg: 'bg-[#34D399]/10',
      border: 'border-[#34D399]/30',
      text: 'text-[#34D399]',
      glow: 'shadow-[0_0_12px_rgba(52,211,153,0.2)]',
    },
    flag_review: {
      label: 'REVIEW',
      icon: AlertTriangle,
      bg: 'bg-[#FBBF24]/10',
      border: 'border-[#FBBF24]/30',
      text: 'text-[#FBBF24]',
      glow: 'shadow-[0_0_12px_rgba(251,191,36,0.2)]',
    },
    block: {
      label: 'BLOCK',
      icon: ShieldAlert,
      bg: 'bg-[#FB7185]/10',
      border: 'border-[#FB7185]/30',
      text: 'text-[#FB7185]',
      glow: 'shadow-[0_0_12px_rgba(251,113,133,0.2)]',
    },
  };

  const config = configs[decision] || configs.allow;
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs font-semibold tracking-wider',
    md: 'px-3 py-1 text-xs font-bold tracking-widest',
    lg: 'px-4 py-1.5 text-sm font-bold tracking-widest',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border uppercase font-mono ${config.bg} ${config.border} ${config.text} ${config.glow} ${sizeClasses[size]}`}
    >
      {showIcon && <Icon className={size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />}
      <span>{config.label}</span>
    </span>
  );
};
