import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/cn';

type LoadingVariant = 'default' | 'compact' | 'inline';

interface LoadingStateProps {
  message?: string;
  description?: string;
  variant?: LoadingVariant;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading…',
  description,
  variant = 'default',
  className,
}) => {
  const isCompact = variant === 'compact';
  const isInline = variant === 'inline';

  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className={cn(
        'flex items-center text-center',
        isInline
          ? 'gap-3 py-3 px-4 rounded-xl bg-slate-900/20 border border-slate-900'
          : isCompact
            ? 'flex-col justify-center py-10 px-4 space-y-3 rounded-2xl bg-slate-900/10 border border-slate-900'
            : 'flex-col justify-center py-20 px-4 space-y-4 rounded-2xl bg-slate-900/10 border border-slate-900',
        className
      )}
    >
      <div className={cn('relative flex items-center justify-center', isInline && 'flex-shrink-0')}>
        {!isInline && (
          <div className="w-12 h-12 rounded-full border border-indigo-500/10 bg-indigo-500/5 animate-ping absolute" />
        )}
        <Loader2
          className={cn(
            'text-indigo-400 animate-spin',
            isInline ? 'w-5 h-5' : isCompact ? 'w-7 h-7' : 'w-8 h-8'
          )}
          aria-hidden="true"
        />
      </div>
      <div className={cn('space-y-1', isInline && 'text-left')}>
        <p className={cn('font-semibold text-slate-300', isInline ? 'text-xs' : 'text-sm')}>
          {message}
        </p>
        {description && (
          <p className="text-xs text-slate-500 leading-relaxed">{description}</p>
        )}
        {!description && !isInline && (
          <p className="text-xs text-slate-500">
            AI-assisted analysis in progress. Results require human review.
          </p>
        )}
      </div>
      <span className="sr-only">{message}</span>
    </div>
  );
};
