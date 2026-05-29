import React from 'react';
import Link from 'next/link';
import { AnalysisJob } from './types';
import { StatusBadge } from '@/components/status-badge';
import { FileText, Clock, Trash2, ArrowRight } from 'lucide-react';

interface AnalysisJobCardProps {
  job: AnalysisJob;
  onDelete: (id: string) => void;
}

export const AnalysisJobCard: React.FC<AnalysisJobCardProps> = ({ job, onDelete }) => {
  const formattedDate = new Date(job.created_at).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  return (
    <div className="group relative bg-slate-900/30 hover:bg-slate-900/50 border border-slate-800 hover:border-indigo-500/30 rounded-2xl p-5 shadow-sm hover:shadow-indigo-500/5 transition-all duration-300">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
          <Clock className="w-3.5 h-3.5 text-slate-600" />
          <span>{formattedDate}</span>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={job.status} />
          <button
            onClick={(e) => {
              e.preventDefault();
              onDelete(job.id);
            }}
            className="p-1.5 rounded-lg border border-transparent hover:border-slate-800 text-slate-500 hover:text-rose-400 hover:bg-rose-500/5 transition-all"
            title="Delete analysis from history"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="space-y-3 mb-5">
        <div className="flex items-start gap-2.5 min-w-0">
          <FileText className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block leading-none mb-0.5">Original Contract</span>
            <span className="text-sm font-semibold text-slate-300 truncate block" title={job.original_filename}>
              {job.original_filename || 'Unknown Document'}
            </span>
          </div>
        </div>

        <div className="flex items-start gap-2.5 min-w-0">
          <FileText className="w-4 h-4 text-indigo-500/70 mt-0.5 flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-500/70 block leading-none mb-0.5">Amendment / Addendum</span>
            <span className="text-sm font-semibold text-slate-300 truncate block" title={job.amendment_filename}>
              {job.amendment_filename || 'Unknown Document'}
            </span>
          </div>
        </div>
      </div>

      <div className="pt-3.5 border-t border-slate-900 flex items-center justify-between text-xs">
        <span className="font-mono text-slate-600 text-[10px] select-all uppercase">
          ID: {job.id.substring(0, 12)}...
        </span>
        <Link
          href={`/analyses/${job.id}`}
          className="flex items-center gap-1 font-bold text-indigo-400 group-hover:text-indigo-300 transition-colors"
        >
          View Analysis
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>

      {job.status === 'FAILED' && job.error_message && (
        <div className="mt-3.5 p-2.5 rounded-xl bg-rose-500/5 border border-rose-500/10 text-[10px] text-rose-400 font-medium leading-relaxed">
          <strong>Error Details:</strong> {job.error_message}
        </div>
      )}
    </div>
  );
};
