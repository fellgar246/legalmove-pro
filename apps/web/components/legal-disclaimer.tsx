import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { cn } from '@/lib/cn';
import { UX_MESSAGES } from '@/lib/ux-messages';

interface LegalDisclaimerProps {
  className?: string;
}

export const LegalDisclaimer: React.FC<LegalDisclaimerProps> = ({ className }) => {
  return (
    <aside
      className={cn(
        'flex items-start gap-3 bg-amber-500/5 border border-amber-500/10 rounded-2xl p-4 text-[11px] sm:text-xs text-amber-400 leading-relaxed',
        className
      )}
      aria-label="Legal disclaimer"
    >
      <ShieldAlert className="w-5 h-5 flex-shrink-0 text-amber-400 mt-0.5" aria-hidden="true" />
      <p>{UX_MESSAGES.disclaimer}</p>
    </aside>
  );
};
