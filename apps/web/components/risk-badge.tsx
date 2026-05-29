import React from 'react';
import { ShieldAlert, ShieldCheck, ShieldAlert as ShieldIcon, HelpCircle } from 'lucide-react';
import { cn } from '@/lib/cn';

export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';

interface RiskBadgeProps {
  level: RiskLevel | string;
  className?: string;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, className }) => {
  const normLevel = (level || '').toUpperCase() as RiskLevel;

  switch (normLevel) {
    case 'CRITICAL':
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-rose-600 text-white shadow-sm border border-rose-500 animate-pulse select-none",
            className
          )}
        >
          <ShieldAlert className="w-3 h-3" />
          Critical Risk
        </span>
      );
    case 'HIGH':
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/20 select-none",
            className
          )}
        >
          <ShieldAlert className="w-3 h-3" />
          High Risk
        </span>
      );
    case 'MEDIUM':
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 select-none",
            className
          )}
        >
          <ShieldIcon className="w-3 h-3" />
          Medium Risk
        </span>
      );
    case 'LOW':
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 select-none",
            className
          )}
        >
          <ShieldCheck className="w-3 h-3" />
          Low Risk
        </span>
      );
    default:
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[10px] font-semibold uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700/50 select-none",
            className
          )}
        >
          <HelpCircle className="w-3 h-3" />
          Unknown Risk
        </span>
      );
  }
};
