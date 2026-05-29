import React from 'react';
import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/cn';
import { UX_MESSAGES } from '@/lib/ux-messages';
import type { ValidationStatus } from './types';

interface ValidationWarningsProps {
  status: ValidationStatus | string;
  warnings?: string[];
  className?: string;
}

function StatusBadge({ status }: { status: string }) {
  const norm = (status || 'VALID').toUpperCase();

  if (norm === 'INVALID') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/20">
        <XCircle className="h-3 w-3" />
        Invalid
      </span>
    );
  }

  if (norm === 'VALID_WITH_WARNINGS') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <AlertTriangle className="h-3 w-3" />
        Valid with warnings
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
      <CheckCircle2 className="h-3 w-3" />
      Valid
    </span>
  );
}

export const ValidationWarnings: React.FC<ValidationWarningsProps> = ({
  status,
  warnings = [],
  className,
}) => {
  const hasWarnings = warnings.length > 0;

  return (
    <div
      className={cn(
        'rounded-2xl border p-5 space-y-3',
        hasWarnings
          ? 'bg-amber-500/5 border-amber-500/10'
          : 'bg-slate-900/10 border-slate-900',
        className
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <h4 className="text-xs font-bold text-slate-200 flex items-center gap-1.5 uppercase tracking-wider">
          {hasWarnings ? (
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          ) : (
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          )}
          Validation
        </h4>
        <StatusBadge status={status} />
      </div>

      {hasWarnings ? (
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-300">
          {warnings.map((warning, index) => (
            <li
              key={index}
              className="flex items-start gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-900 leading-relaxed"
            >
              <span className="text-amber-500 font-bold mt-0.5">•</span>
              <span className="text-[11px]">{warning}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-xs text-slate-500">{UX_MESSAGES.empty.noWarnings.description}</p>
      )}
    </div>
  );
};
