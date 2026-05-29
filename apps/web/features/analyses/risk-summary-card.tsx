import React from 'react';
import { AnalysisSummary, LegalChange, RiskLevel } from './types';
import { RiskBadge } from '@/components/risk-badge';
import { EmptyState } from '@/components/empty-state';
import { UX_MESSAGES } from '@/lib/ux-messages';
import { ShieldAlert } from 'lucide-react';

interface RiskSummaryCardProps {
  summary: AnalysisSummary;
  changes: LegalChange[];
}

function countByRisk(changes: LegalChange[], level: RiskLevel): number {
  return changes.filter((c) => c.risk_level === level).length;
}

export const RiskSummaryCard: React.FC<RiskSummaryCardProps> = ({ summary, changes }) => {
  const breakdown: { level: RiskLevel; count: number }[] = [
    { level: 'CRITICAL', count: countByRisk(changes, 'CRITICAL') },
    { level: 'HIGH', count: countByRisk(changes, 'HIGH') },
    { level: 'MEDIUM', count: countByRisk(changes, 'MEDIUM') },
    { level: 'LOW', count: countByRisk(changes, 'LOW') },
    { level: 'UNKNOWN', count: countByRisk(changes, 'UNKNOWN') },
  ];

  if (changes.length === 0) {
    return (
      <EmptyState
        title={UX_MESSAGES.empty.noChanges.title}
        description={UX_MESSAGES.empty.noChanges.description}
        icon={<ShieldAlert className="h-5 w-5" aria-hidden="true" />}
      />
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/20 p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 uppercase tracking-wider">
          <ShieldAlert className="h-4 w-4 text-indigo-400" />
          Risk summary
        </h3>
        <div className="flex items-center gap-3 text-xs">
          <RiskBadge level={summary.overall_risk_level} />
          <span className="text-slate-500">
            {summary.high_risk_changes} high-risk change{summary.high_risk_changes !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {breakdown.map(({ level, count }) => (
          <div
            key={level}
            className="rounded-xl border border-slate-900 bg-slate-950/40 p-3 text-center space-y-1"
          >
            <RiskBadge level={level} className="mx-auto" />
            <span className="block text-xl font-bold text-slate-100">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
