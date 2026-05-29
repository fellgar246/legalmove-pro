'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { cn } from '@/lib/cn';

interface RawJsonViewerProps {
  data: unknown;
  className?: string;
}

export const RawJsonViewer: React.FC<RawJsonViewerProps> = ({ data, className }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy JSON:', err);
    }
  };

  return (
    <div className={cn("border border-slate-900 rounded-2xl overflow-hidden bg-slate-900/10", className)}>
      {/* Header */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="px-5 py-4 flex items-center justify-between cursor-pointer hover:bg-slate-900/20 select-none transition-colors"
      >
        <div className="flex items-center gap-2">
          {isOpen ? (
            <ChevronDown className="w-4 h-4 text-indigo-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-500" />
          )}
          <span className="text-xs sm:text-sm font-bold text-slate-300">Raw JSON Payload (Engineer Debugger)</span>
        </div>
        <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded select-none">
          {isOpen ? 'Collapse' : 'Expand'}
        </span>
      </div>

      {/* Code Area */}
      {isOpen && (
        <div className="border-t border-slate-900 bg-slate-950 p-4 relative animate-slide-down">
          <button
            onClick={handleCopy}
            className="absolute right-4 top-4 p-2 rounded-lg border border-slate-900 hover:border-slate-800 text-slate-400 hover:text-slate-200 bg-slate-900/60 active:scale-95 transition-all"
            title="Copy raw JSON payload"
          >
            {copied ? (
              <Check className="w-4 h-4 text-emerald-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>

          <pre className="text-xs font-mono text-slate-300 max-h-[350px] overflow-x-auto overflow-y-auto leading-relaxed select-all">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
