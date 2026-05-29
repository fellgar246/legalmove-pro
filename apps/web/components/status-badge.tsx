import React from 'react';
import { Clock, Loader2, CheckCircle2, Eye, AlertCircle, HelpCircle } from 'lucide-react';
import { cn } from '@/lib/cn';

export type JobStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'NEEDS_REVIEW';

interface StatusBadgeProps {
  status: JobStatus | string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  const normStatus = (status || '').toUpperCase() as JobStatus;

  switch (normStatus) {
    case 'QUEUED':
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/15 select-none",
            className
          )}
        >
          <Clock className="w-3.5 h-3.5 animate-pulse" />
          Queued
        </span>
      );
    case 'PROCESSING':
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/15 select-none",
            className
          )}
        >
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          Processing
        </span>
      );
    case 'COMPLETED':
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/15 select-none",
            className
          )}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Completed
        </span>
      );
    case 'NEEDS_REVIEW':
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-orange-500/10 text-orange-400 border border-orange-500/15 select-none",
            className
          )}
        >
          <Eye className="w-3.5 h-3.5 animate-pulse" />
          Needs Review
        </span>
      );
    case 'FAILED':
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/15 select-none",
            className
          )}
        >
          <AlertCircle className="w-3.5 h-3.5 animate-bounce" />
          Failed
        </span>
      );
    default:
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700/50 select-none",
            className
          )}
        >
          <HelpCircle className="w-3.5 h-3.5" />
          {status || 'Unknown'}
        </span>
      );
  }
};
