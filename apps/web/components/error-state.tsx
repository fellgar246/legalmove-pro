import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message,
  onRetry,
  retryLabel = 'Try again',
  className,
}) => {
  return (
    <div
      role="alert"
      aria-live="assertive"
      className={cn(
        'flex flex-col items-center justify-center py-16 px-4 text-center space-y-5 rounded-2xl bg-rose-500/5 border border-rose-500/10 max-w-xl mx-auto',
        className
      )}
    >
      <div
        className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400"
        aria-hidden="true"
      >
        <AlertCircle className="w-6 h-6" />
      </div>
      <div className="space-y-1.5">
        <h3 className="text-md font-bold text-rose-300">{title}</h3>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed max-w-sm">{message}</p>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          aria-label={retryLabel}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-slate-100 hover:bg-slate-800 active:scale-95 transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
          {retryLabel}
        </button>
      )}
    </div>
  );
};
