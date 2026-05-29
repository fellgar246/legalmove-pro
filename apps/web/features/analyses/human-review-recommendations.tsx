import React from 'react';
import { ListTodo, Eye } from 'lucide-react';
import { cn } from '@/lib/cn';
import { EmptyState } from '@/components/empty-state';
import { UX_MESSAGES } from '@/lib/ux-messages';

interface HumanReviewRecommendationsProps {
  recommendations: string[];
  requiresHumanReview?: boolean;
  className?: string;
}

export const HumanReviewRecommendations: React.FC<HumanReviewRecommendationsProps> = ({
  recommendations = [],
  requiresHumanReview = false,
  className,
}) => {
  return (
    <div
      className={cn(
        'rounded-2xl border border-slate-800 bg-slate-900/20 p-6 space-y-4',
        className
      )}
    >
      <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 uppercase tracking-wider">
        <ListTodo className="h-4 w-4 text-indigo-400" aria-hidden="true" />
        Human review recommendations
      </h3>

      {requiresHumanReview && (
        <div
          className="flex items-start gap-2.5 rounded-xl border border-amber-500/15 bg-amber-500/5 p-3 text-xs text-amber-300"
          role="status"
        >
          <Eye className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <span>
            This AI-assisted analysis flagged items that need review by a qualified human.
          </span>
        </div>
      )}

      {recommendations.length === 0 ? (
        <EmptyState
          title={UX_MESSAGES.empty.noRecommendations.title}
          description={UX_MESSAGES.empty.noRecommendations.description}
          className="py-8 border-none bg-transparent"
        />
      ) : (
        <ul className="space-y-2">
          {recommendations.map((recommendation, index) => (
            <li
              key={index}
              className="flex items-start gap-2.5 rounded-xl border border-slate-900 bg-slate-950/40 p-3 text-xs text-slate-300 leading-relaxed"
            >
              <span className="text-indigo-400 font-bold mt-0.5">{index + 1}.</span>
              <span>{recommendation}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
