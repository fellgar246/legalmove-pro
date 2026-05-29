'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { StatusBadge } from '@/components/status-badge';
import { LoadingState } from '@/components/loading-state';
import { ErrorState } from '@/components/error-state';
import { LegalDisclaimer } from '@/components/legal-disclaimer';
import { formatApiError } from '@/lib/format-api-error';
import { UX_MESSAGES } from '@/lib/ux-messages';
import { ApiClientError } from '@/lib/api-client';
import { getAnalysis, getAnalysisResult } from './api';
import { AnalysisStatusCard } from './analysis-status-card';
import { ExecutiveSummaryCard } from './executive-summary-card';
import { RiskSummaryCard } from './risk-summary-card';
import { ChangesTable } from './changes-table';
import { ValidationWarnings } from './validation-warnings';
import { HumanReviewRecommendations } from './human-review-recommendations';
import { RawJsonViewer } from './raw-json-viewer';
import { normalizeToViewModel } from './report-utils';
import type { AnalysisJob, AnalysisResultResponse, AnalysisStatus, AnalysisViewModel } from './types';

const POLL_INTERVAL_MS = 3000;

interface AnalysisDetailClientProps {
  analysisId: string;
}

function shortId(id: string): string {
  return id.substring(0, 8);
}

function shouldLoadResult(status: AnalysisStatus): boolean {
  return status === 'COMPLETED' || status === 'NEEDS_REVIEW';
}

function isTerminal(status: AnalysisStatus): boolean {
  return status === 'COMPLETED' || status === 'FAILED' || status === 'NEEDS_REVIEW';
}

export const AnalysisDetailClient: React.FC<AnalysisDetailClientProps> = ({ analysisId }) => {
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [viewModel, setViewModel] = useState<AnalysisViewModel | null>(null);
  const [rawResult, setRawResult] = useState<AnalysisResultResponse | null>(null);
  const [jobLoading, setJobLoading] = useState(true);
  const [resultLoading, setResultLoading] = useState(false);
  const [jobError, setJobError] = useState<string | null>(null);
  const [resultError, setResultError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  const refreshResult = useCallback(async () => {
    setResultLoading(true);
    setResultError(null);
    try {
      const response = await getAnalysisResult(analysisId);
      setRawResult(response);
      setViewModel(normalizeToViewModel(response.result));
    } catch (err) {
      if (err instanceof ApiClientError && (err.status === 404 || err.status === 202)) {
        setResultError(UX_MESSAGES.error.resultNotAvailable);
        return;
      }
      setResultError(formatApiError(err, UX_MESSAGES.error.resultNotAvailable));
    } finally {
      setResultLoading(false);
    }
  }, [analysisId]);

  const refreshJob = useCallback(
    async (manual = false) => {
      if (manual) setIsRefreshing(true);
      try {
        const data = await getAnalysis(analysisId);
        setJob(data);
        setJobError(null);

        if (isTerminal(data.status)) {
          stopPolling();
          if (shouldLoadResult(data.status)) {
            await refreshResult();
          }
        }
      } catch (err) {
        setJobError(formatApiError(err, UX_MESSAGES.error.notFound));
        if (err instanceof ApiClientError && err.status === 404) {
          stopPolling();
        }
      } finally {
        setJobLoading(false);
        if (manual) setIsRefreshing(false);
      }
    },
    [analysisId, refreshResult, stopPolling]
  );

  useEffect(() => {
    let active = true;

    const poll = async () => {
      if (!active) return;
      await refreshJob(false);
    };

    poll();
    pollIntervalRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      active = false;
      stopPolling();
    };
  }, [analysisId, refreshJob, stopPolling]);

  const handleManualRefresh = () => {
    void refreshJob(true);
  };

  if (jobLoading && !job) {
    return (
      <LoadingState
        message={UX_MESSAGES.loading.analysisJob}
        description="Checking the status of your AI-assisted analysis."
      />
    );
  }

  if (jobError && !job) {
    return (
      <div className="py-12">
        <ErrorState
          title="Analysis not found"
          message={jobError}
          onRetry={handleManualRefresh}
        />
      </div>
    );
  }

  if (!job) {
    return null;
  }

  const showResult = shouldLoadResult(job.status);
  const isProcessing = job.status === 'QUEUED' || job.status === 'PROCESSING';

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-900">
        <div className="space-y-1">
          <Link
            href="/analyses"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors group mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
            Back to analyses
          </Link>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-100 flex items-center flex-wrap gap-2">
            AI-assisted analysis
            <span className="font-mono text-xs text-slate-500 font-normal">{shortId(job.id)}</span>
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleManualRefresh}
            disabled={isRefreshing}
            aria-label="Refresh analysis status"
            aria-busy={isRefreshing}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-800 text-xs font-semibold text-slate-300 hover:text-slate-100 hover:bg-slate-900 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} aria-hidden="true" />
            Refresh
          </button>
          <StatusBadge status={job.status} />
        </div>
      </div>

      <AnalysisStatusCard job={job} isRefreshing={isRefreshing} />

      {isProcessing && (
        <LoadingState
          variant="compact"
          message={UX_MESSAGES.loading.processing}
          description="This page updates automatically. Findings will require human review."
        />
      )}

      {job.status === 'FAILED' && (
        <ErrorState
          title={UX_MESSAGES.error.analysisFailed}
          message={
            job.error_message ||
            'The AI-assisted analysis could not be completed. Try starting a new analysis.'
          }
          onRetry={handleManualRefresh}
        />
      )}

      {showResult && resultLoading && !viewModel && (
        <LoadingState
          message={UX_MESSAGES.loading.analysisResult}
          description="Preparing the comparison report for your review."
        />
      )}

      {showResult && resultError && !resultLoading && (
        <ErrorState
          title="Result not available"
          message={resultError}
          onRetry={() => void refreshResult()}
        />
      )}

      {showResult && viewModel && !resultLoading && !resultError && (
        <div className="space-y-6">
          <ExecutiveSummaryCard summary={viewModel.summary} />
          <RiskSummaryCard summary={viewModel.summary} changes={viewModel.changes} />
          <ChangesTable changes={viewModel.changes} />
          <ValidationWarnings
            status={viewModel.validation.status}
            warnings={viewModel.validation.warnings}
          />
          <HumanReviewRecommendations
            recommendations={viewModel.human_review_recommendations}
            requiresHumanReview={viewModel.summary.requires_human_review}
          />
          <RawJsonViewer data={rawResult ?? viewModel} />
          <LegalDisclaimer />
        </div>
      )}
    </div>
  );
};
