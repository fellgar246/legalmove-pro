'use client';

import React, { useMemo, useState } from 'react';
import { LegalChange } from './types';
import { RiskBadge } from '@/components/risk-badge';
import { EmptyState } from '@/components/empty-state';
import { UX_MESSAGES } from '@/lib/ux-messages';
import {
  ChevronDown,
  ChevronUp,
  Search,
  SlidersHorizontal,
} from 'lucide-react';
import { cn } from '@/lib/cn';

interface ChangesTableProps {
  changes?: LegalChange[];
}

function formatChangeType(type: string | undefined): string {
  if (!type) return '—';
  return type.charAt(0) + type.slice(1).toLowerCase();
}

function getConfidenceBadge(confidence: string | undefined) {
  const baseClass = 'px-2 py-0.5 rounded text-[10px] font-semibold uppercase';
  switch ((confidence || '').toUpperCase()) {
    case 'HIGH':
      return (
        <span className={cn(baseClass, 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/15')}>
          High
        </span>
      );
    case 'MEDIUM':
      return (
        <span className={cn(baseClass, 'bg-amber-500/10 text-amber-400 border border-amber-500/15')}>
          Medium
        </span>
      );
    case 'LOW':
      return (
        <span className={cn(baseClass, 'bg-rose-500/10 text-rose-400 border border-rose-500/15')}>
          Low
        </span>
      );
    default:
      return <span className="text-slate-500 text-xs">—</span>;
  }
}

function beforeTextLabel(change: LegalChange): string {
  if (change.before_text) return change.before_text;
  if (change.change_type === 'ADDITION') return 'Not applicable';
  return 'Not available';
}

function afterTextLabel(change: LegalChange): string {
  if (change.after_text) return change.after_text;
  if (change.change_type === 'DELETION') return 'Not applicable';
  return 'Not available';
}

function quoteOrFallback(quote: string | null | undefined): string {
  return quote?.trim() ? quote : 'Not available';
}

export const ChangesTable: React.FC<ChangesTableProps> = ({ changes = [] }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [reviewFilter, setReviewFilter] = useState('ALL');

  const filteredChanges = useMemo(() => {
    return changes.filter((c) => {
      const matchSearch =
        `${c.legal_topic ?? ''} ${c.section_reference ?? ''} ${c.summary ?? ''} ${c.change_id ?? ''}`
          .toLowerCase()
          .includes(search.toLowerCase());
      const matchRisk = riskFilter === 'ALL' || c.risk_level === riskFilter;
      const matchType = typeFilter === 'ALL' || c.change_type === typeFilter;
      const matchReview =
        reviewFilter === 'ALL' ||
        (reviewFilter === 'YES' && c.requires_human_review) ||
        (reviewFilter === 'NO' && !c.requires_human_review);
      return matchSearch && matchRisk && matchType && matchReview;
    });
  }, [changes, search, riskFilter, typeFilter, reviewFilter]);

  const toggleRow = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  if (changes.length === 0) {
    return (
      <EmptyState
        title={UX_MESSAGES.empty.noChanges.title}
        description={UX_MESSAGES.empty.noChanges.description}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-slate-900/30 border border-slate-900 p-4 rounded-2xl space-y-3">
        <div className="flex flex-col md:flex-row gap-3 items-center">
          <div className="relative w-full md:flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="search"
              aria-label="Search changes"
              placeholder="Search by topic, section, summary..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500/50"
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-400" />
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-[11px] text-slate-300 rounded-lg px-2 py-1.5 outline-none"
            >
              <option value="ALL">All risks</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-[11px] text-slate-300 rounded-lg px-2 py-1.5 outline-none"
            >
              <option value="ALL">All types</option>
              <option value="ADDITION">Addition</option>
              <option value="DELETION">Deletion</option>
              <option value="MODIFICATION">Modification</option>
              <option value="REPLACEMENT">Replacement</option>
            </select>
            <select
              value={reviewFilter}
              onChange={(e) => setReviewFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-[11px] text-slate-300 rounded-lg px-2 py-1.5 outline-none"
            >
              <option value="ALL">All review</option>
              <option value="YES">Needs review</option>
              <option value="NO">No review</option>
            </select>
          </div>
        </div>
        <p className="text-xs text-slate-500">
          Showing {filteredChanges.length} of {changes.length} changes
        </p>
      </div>

      {filteredChanges.length === 0 ? (
        <EmptyState
          title={UX_MESSAGES.empty.noFilteredChanges.title}
          description={UX_MESSAGES.empty.noFilteredChanges.description}
          className="py-12"
        />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-900">
          <table className="w-full min-w-[900px] text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-900">
              <tr>
                <th className="px-3 py-3 font-bold text-slate-400 uppercase tracking-wider w-8" />
                <th className="px-3 py-3 font-bold text-slate-400 uppercase tracking-wider">Type</th>
                <th className="px-3 py-3 font-bold text-slate-400 uppercase tracking-wider">Topic</th>
                <th className="px-3 py-3 font-bold text-slate-400 uppercase tracking-wider">Section</th>
                <th className="px-3 py-3 font-bold text-slate-400 uppercase tracking-wider">Risk</th>
                <th className="px-3 py-3 font-bold text-slate-400 uppercase tracking-wider">Confidence</th>
                <th className="px-3 py-3 font-bold text-slate-400 uppercase tracking-wider min-w-[200px]">Summary</th>
                <th className="px-3 py-3 font-bold text-slate-400 uppercase tracking-wider">Human review</th>
              </tr>
            </thead>
            <tbody>
              {filteredChanges.map((change) => {
                const rowId = change.change_id || `${change.legal_topic}-${change.section_reference}`;
                const isExpanded = expandedId === rowId;

                return (
                  <React.Fragment key={rowId}>
                    <tr
                      onClick={() => toggleRow(rowId)}
                      className={cn(
                        'border-b border-slate-900 cursor-pointer transition-colors',
                        isExpanded ? 'bg-slate-900/30' : 'bg-slate-900/10 hover:bg-slate-900/20'
                      )}
                    >
                      <td className="px-3 py-3 text-slate-500">
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </td>
                      <td className="px-3 py-3 text-slate-300 font-medium">
                        {formatChangeType(change.change_type)}
                      </td>
                      <td className="px-3 py-3 text-slate-300 max-w-[140px] truncate" title={change.legal_topic}>
                        {change.legal_topic ?? '—'}
                      </td>
                      <td className="px-3 py-3 text-slate-400 max-w-[120px] truncate" title={change.section_reference}>
                        {change.section_reference ?? '—'}
                      </td>
                      <td className="px-3 py-3">
                        <RiskBadge level={change.risk_level ?? 'UNKNOWN'} />
                      </td>
                      <td className="px-3 py-3">{getConfidenceBadge(change.confidence)}</td>
                      <td className="px-3 py-3 text-slate-300 max-w-[240px] truncate" title={change.summary}>
                        {change.summary ?? '—'}
                      </td>
                      <td className="px-3 py-3">
                        {change.requires_human_review ? (
                          <span className="text-amber-400 font-semibold">Yes</span>
                        ) : (
                          <span className="text-slate-500">No</span>
                        )}
                      </td>
                    </tr>

                    {isExpanded && (
                      <tr className="bg-slate-950/60 border-b border-slate-900">
                        <td colSpan={8} className="px-4 py-4 space-y-4">
                          {change.impact_explanation && (
                            <div className="rounded-xl border border-amber-500/10 bg-amber-500/5 p-3">
                              <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider block mb-1">
                                Impact explanation
                              </span>
                              <p className="text-xs text-slate-300 leading-relaxed">
                                {change.impact_explanation}
                              </p>
                            </div>
                          )}

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                                Before text
                              </span>
                              <div
                                className={cn(
                                  'rounded-xl border p-3 text-xs leading-relaxed whitespace-pre-wrap',
                                  change.before_text
                                    ? 'border-slate-800 bg-slate-900/40 text-slate-300'
                                    : 'border-slate-900 bg-slate-950/40 text-slate-500 italic'
                                )}
                              >
                                {beforeTextLabel(change)}
                              </div>
                            </div>
                            <div>
                              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                                After text
                              </span>
                              <div
                                className={cn(
                                  'rounded-xl border p-3 text-xs leading-relaxed whitespace-pre-wrap',
                                  change.after_text
                                    ? 'border-slate-800 bg-slate-900/40 text-slate-300'
                                    : 'border-slate-900 bg-slate-950/40 text-slate-500 italic'
                                )}
                              >
                                {afterTextLabel(change)}
                              </div>
                            </div>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                                Original quote
                              </span>
                              <p className="text-xs text-slate-400 italic leading-relaxed">
                                {quoteOrFallback(change.evidence?.original_quote)}
                              </p>
                            </div>
                            <div>
                              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                                Amendment quote
                              </span>
                              <p className="text-xs text-slate-400 italic leading-relaxed">
                                {quoteOrFallback(change.evidence?.amendment_quote)}
                              </p>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
