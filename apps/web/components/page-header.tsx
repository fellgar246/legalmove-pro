import React from 'react';
import { cn } from '@/lib/cn';

interface PageHeaderProps {
  title: string;
  description?: string;
  children?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  children,
  className,
}) => {
  return (
    <div
      className={cn(
        "flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-900",
        className
      )}
    >
      <div className="space-y-1.5 max-w-2xl">
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-100">
          {title}
        </h1>
        {description && (
          <p className="text-sm text-slate-400 leading-relaxed font-medium">
            {description}
          </p>
        )}
      </div>
      {children && (
        <div className="flex items-center gap-3 flex-shrink-0">
          {children}
        </div>
      )}
    </div>
  );
};
