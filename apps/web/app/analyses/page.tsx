'use client';

import React, { useEffect, useState } from 'react';
import { PageHeader } from '@/components/page-header';
import { LoadingState } from '@/components/loading-state';
import { ErrorState } from '@/components/error-state';
import { EmptyState } from '@/components/empty-state';
import { getAnalyses, deleteAnalysis } from '@/features/analyses/api';
import { AnalysisJob } from '@/features/analyses/types';
import { AnalysisJobCard } from '@/features/analyses/analysis-job-card';
import { formatApiError } from '@/lib/format-api-error';
import { UX_MESSAGES } from '@/lib/ux-messages';
import { Plus, RefreshCw, FolderOpen, Server } from 'lucide-react';
import Link from 'next/link';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';

export default function AnalysesDashboard() {
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    fetchJobs();
    checkBackend();
  }, []);

  const checkBackend = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      setApiOnline(res.ok);
    } catch {
      setApiOnline(false);
    }
  };

  const fetchJobs = async () => {
    setLoading(true);
    setError('');
    try {
      const list = await getAnalyses();
      setJobs(list);
    } catch (err) {
      setError(formatApiError(err, 'Failed to load analyses.'));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Remove this analysis from your local history?')) {
      try {
        const success = await deleteAnalysis(id);
        if (success) {
          setJobs((prev) => prev.filter((j) => j.id !== id));
        }
      } catch (err) {
        console.error('Delete failed:', err);
      }
    }
  };

  const apiOfflineMessage =
    apiOnline === false ? UX_MESSAGES.error.apiOffline : undefined;

  return (
    <div className="space-y-8 animate-fade-in">
      <PageHeader
        title="Analyses"
        description="Track AI-assisted contract comparisons. Review all findings with a qualified human before acting on them."
      >
        <div className="flex items-center gap-3">
          <div
            className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-400"
            role="status"
            aria-live="polite"
          >
            <Server
              className={`w-3.5 h-3.5 ${apiOnline ? 'text-emerald-500' : apiOnline === false ? 'text-rose-500' : 'text-slate-500 animate-spin'}`}
              aria-hidden="true"
            />
            API:{' '}
            {apiOnline === true ? (
              <span className="text-emerald-400 font-bold">Online</span>
            ) : apiOnline === false ? (
              <span className="text-rose-400 font-bold">Offline</span>
            ) : (
              <span>Checking…</span>
            )}
          </div>

          <button
            type="button"
            onClick={() => {
              fetchJobs();
              checkBackend();
            }}
            disabled={loading}
            aria-label="Refresh analyses list"
            aria-busy={loading}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-800 text-xs font-semibold text-slate-300 hover:text-slate-100 hover:bg-slate-900 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
            Refresh
          </button>

          <Link
            href="/analyses/new"
            className="flex items-center gap-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" aria-hidden="true" />
            New analysis
          </Link>
        </div>
      </PageHeader>

      {apiOfflineMessage && (
        <ErrorState
          title="API unavailable"
          message={apiOfflineMessage}
          onRetry={() => {
            checkBackend();
            fetchJobs();
          }}
          className="max-w-none"
        />
      )}

      {loading ? (
        <LoadingState
          message={UX_MESSAGES.loading.analysesList}
          description="Fetching your saved AI-assisted analyses."
        />
      ) : error && !apiOfflineMessage ? (
        <ErrorState
          title="Could not load analyses"
          message={error}
          onRetry={fetchJobs}
        />
      ) : jobs.length === 0 ? (
        <EmptyState
          title={UX_MESSAGES.empty.noAnalyses.title}
          description={UX_MESSAGES.empty.noAnalyses.description}
          icon={<FolderOpen className="w-5 h-5" aria-hidden="true" />}
          action={
            <Link
              href="/analyses/new"
              className="inline-flex items-center gap-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl transition-all"
            >
              <Plus className="w-4 h-4" aria-hidden="true" />
              Start first analysis
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {jobs.map((job) => (
            <AnalysisJobCard key={job.id} job={job} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}
