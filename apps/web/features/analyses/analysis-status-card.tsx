import React from 'react';
import { AnalysisJob } from './types';
import { StatusBadge } from '@/components/status-badge';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileText,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/cn';

interface AnalysisStatusCardProps {
  job: AnalysisJob;
  isRefreshing?: boolean;
}

export const AnalysisStatusCard: React.FC<AnalysisStatusCardProps> = ({
  job,
  isRefreshing = false,
}) => {
  const formattedDate = new Date(job.created_at).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  const isPending = job.status === 'QUEUED' || job.status === 'PROCESSING';

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/20 p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-sm font-bold text-slate-200">Analysis status</h2>
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <Clock className="h-3.5 w-3.5 text-slate-600" />
            <span>Created {formattedDate}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isRefreshing && (
            <Loader2 className="h-4 w-4 animate-spin text-indigo-400" aria-hidden="true" />
          )}
          <StatusBadge status={job.status} />
        </div>
      </div>

      {(job.original_filename || job.amendment_filename) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          {job.original_filename && (
            <div className="flex items-start gap-2.5 min-w-0">
              <FileText className="h-4 w-4 text-slate-500 mt-0.5 flex-shrink-0" />
              <div className="min-w-0">
                <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block mb-0.5">
                  Original contract
                </span>
                <span className="text-sm text-slate-300 truncate block" title={job.original_filename}>
                  {job.original_filename}
                </span>
              </div>
            </div>
          )}
          {job.amendment_filename && (
            <div className="flex items-start gap-2.5 min-w-0">
              <FileText className="h-4 w-4 text-indigo-500/70 mt-0.5 flex-shrink-0" />
              <div className="min-w-0">
                <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-500/70 block mb-0.5">
                  Amendment
                </span>
                <span className="text-sm text-slate-300 truncate block" title={job.amendment_filename}>
                  {job.amendment_filename}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {isPending && (
        <div className="flex items-start gap-3 rounded-xl border border-indigo-500/15 bg-indigo-500/5 p-4">
          <Loader2 className="h-5 w-5 animate-spin text-indigo-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="text-sm font-semibold text-slate-200">Running AI-assisted analysis…</p>
            <p className="text-xs text-slate-500 leading-relaxed">
              {job.status === 'QUEUED'
                ? 'Your request is queued. Results will appear here and require human review.'
                : 'Comparing both documents and extracting changes. This is not legal advice.'}
            </p>
          </div>
        </div>
      )}

      {job.status === 'COMPLETED' && (
        <div className="flex items-start gap-3 rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-4">
          <CheckCircle2 className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-slate-300">
            AI-assisted analysis completed. Review the findings below with a qualified human.
          </p>
        </div>
      )}

      {job.status === 'NEEDS_REVIEW' && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-500/15 bg-amber-500/5 p-4">
          <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="text-sm font-semibold text-amber-300">Human review recommended</p>
            <p className="text-xs text-slate-400 leading-relaxed">
              Some findings need verification by a qualified human before you rely on them.
            </p>
          </div>
        </div>
      )}

      {job.status === 'FAILED' && (
        <div
          className={cn(
            'flex items-start gap-3 rounded-xl border border-rose-500/15 bg-rose-500/5 p-4'
          )}
        >
          <AlertCircle className="h-5 w-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="text-sm font-semibold text-rose-300">Analysis failed</p>
            <p className="text-xs text-slate-400 leading-relaxed">
              {job.error_message || 'An internal error occurred during processing.'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
