import React from 'react';
import { AnalysisSummary } from './types';
import { RiskBadge } from '@/components/risk-badge';
import { BookOpen, Eye, Hash, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ExecutiveSummaryCardProps {
  summary: AnalysisSummary;
}

export const ExecutiveSummaryCard: React.FC<ExecutiveSummaryCardProps> = ({ summary }) => {
  const {
    executive_summary,
    overall_risk_level,
    total_changes,
    high_risk_changes,
    requires_human_review,
  } = summary;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/20 border border-slate-900 p-5 rounded-2xl">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Overall risk
          </span>
          <div className="mt-3">
            <RiskBadge level={overall_risk_level} />
          </div>
        </div>

        <div className="bg-slate-900/20 border border-slate-900 p-5 rounded-2xl">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
            <Hash className="h-3 w-3" />
            Total changes
          </span>
          <div className="flex items-baseline gap-1.5 mt-2">
            <span className="text-3xl font-extrabold text-slate-100">{total_changes}</span>
          </div>
        </div>

        <div className="bg-slate-900/20 border border-slate-900 p-5 rounded-2xl">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            High-risk changes
          </span>
          <div className="flex items-baseline gap-1.5 mt-2">
            <span
              className={cn(
                'text-3xl font-extrabold',
                high_risk_changes > 0 ? 'text-rose-400' : 'text-slate-100'
              )}
            >
              {high_risk_changes}
            </span>
          </div>
        </div>

        <div className="bg-slate-900/20 border border-slate-900 p-5 rounded-2xl">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
            <Eye className="h-3 w-3" />
            Human review
          </span>
          <div className="mt-3">
            <span
              className={cn(
                'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border',
                requires_human_review
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/15'
                  : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/15'
              )}
            >
              {requires_human_review ? 'Required' : 'Not required'}
            </span>
          </div>
        </div>
      </div>

      <div className="bg-slate-900/20 border border-slate-800 p-6 rounded-2xl space-y-3">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 uppercase tracking-wider">
          <BookOpen className="w-4 h-4 text-indigo-400" />
          Executive summary
        </h3>
        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
          {executive_summary || 'No executive summary available.'}
        </p>
      </div>
    </div>
  );
};
