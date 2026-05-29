import React from 'react';
import { Inbox } from 'lucide-react';
import { cn } from '@/lib/cn';

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center py-16 px-6 rounded-2xl bg-slate-900/10 border border-dashed border-slate-800',
        className
      )}
      role="status"
    >
      <div className="w-12 h-12 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-center text-slate-500 mb-4">
        {icon ?? <Inbox className="w-5 h-5" aria-hidden="true" />}
      </div>
      <h3 className="text-sm font-bold text-slate-300">{title}</h3>
      {description && (
        <p className="text-xs text-slate-500 max-w-md mt-2 leading-relaxed">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
};
