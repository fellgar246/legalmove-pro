'use client';

import React, { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FileImage, FileText, Play, ShieldAlert, X } from 'lucide-react';
import { cn } from '@/lib/cn';
import { formatApiError } from '@/lib/format-api-error';
import { UX_MESSAGES } from '@/lib/ux-messages';
import { createAnalysisJob } from './api';
import { LoadingState } from '@/components/loading-state';
import { ErrorState } from '@/components/error-state';
import type { DocumentRole } from './types';

const ACCEPTED_MIME_TYPES = [
  'image/png',
  'image/jpeg',
  'image/webp',
  'image/gif',
  'application/pdf',
] as const;

const ACCEPT_ATTR = 'image/png,image/jpeg,image/jpg,image/webp,image/gif,application/pdf';
const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024;

type SlotRole = DocumentRole;

function validateFile(file: File): string | null {
  if (!ACCEPTED_MIME_TYPES.includes(file.type as (typeof ACCEPTED_MIME_TYPES)[number])) {
    return `Unsupported file type "${file.type || 'unknown'}". Allowed: PDF, PNG, JPG, WEBP, GIF.`;
  }
  if (file.size === 0) return 'The selected file is empty.';
  if (file.size > MAX_FILE_SIZE_BYTES) return 'Files must be smaller than 20MB.';
  return null;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface FileSlotProps {
  role: SlotRole;
  inputId: string;
  label: string;
  description: string;
  file: File | null;
  disabled: boolean;
  onSelect: (role: SlotRole, file: File) => void;
  onClear: (role: SlotRole) => void;
}

const FileSlot: React.FC<FileSlotProps> = ({
  role,
  inputId,
  label,
  description,
  file,
  disabled,
  onSelect,
  onClear,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-2">
        <label htmlFor={inputId} className="text-sm font-semibold text-slate-200">
          {label}
        </label>
        <span className="text-[11px] text-slate-500">{description}</span>
      </div>

      <input
        ref={inputRef}
        id={inputId}
        type="file"
        accept={ACCEPT_ATTR}
        disabled={disabled}
        aria-describedby={`${inputId}-hint`}
        className="sr-only"
        onChange={(e) => {
          const selected = e.target.files?.[0];
          if (selected) onSelect(role, selected);
          e.target.value = '';
        }}
      />

      {file ? (
        <div className="flex items-center gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3">
          {file.type === 'application/pdf' ? (
            <FileText className="h-5 w-5 flex-shrink-0 text-emerald-400" aria-hidden="true" />
          ) : (
            <FileImage className="h-5 w-5 flex-shrink-0 text-emerald-400" aria-hidden="true" />
          )}
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-200" title={file.name}>
              {file.name}
            </p>
            <p className="text-[11px] text-slate-500">{formatBytes(file.size)}</p>
          </div>
          <button
            type="button"
            onClick={() => onClear(role)}
            disabled={disabled}
            aria-label={`Remove ${label}`}
            className="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={disabled}
          aria-controls={inputId}
          aria-label={`Choose file for ${label}`}
          className="flex w-full items-center gap-3 rounded-xl border border-dashed border-slate-700 bg-slate-900/30 px-4 py-3 text-left transition-colors hover:border-indigo-500/40 hover:bg-slate-900/50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <FileText className="h-5 w-5 flex-shrink-0 text-slate-500" aria-hidden="true" />
          <span id={`${inputId}-hint`} className="text-sm text-slate-400">
            Choose a file{' '}
            <span className="text-indigo-400">(PDF, PNG, JPG, WEBP, GIF)</span>
          </span>
        </button>
      )}
    </div>
  );
};

export const UploadAnalysisForm: React.FC = () => {
  const router = useRouter();
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [amendmentFile, setAmendmentFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSelect = (role: SlotRole, file: File) => {
    const err = validateFile(file);
    if (err) {
      setValidationError(err);
      return;
    }
    setValidationError(null);
    setSubmitError(null);
    if (role === 'ORIGINAL') setOriginalFile(file);
    else setAmendmentFile(file);
  };

  const handleClear = (role: SlotRole) => {
    setValidationError(null);
    if (role === 'ORIGINAL') setOriginalFile(null);
    else setAmendmentFile(null);
  };

  const startAnalysis = async () => {
    if (!originalFile || !amendmentFile) {
      setValidationError('Please select both the original contract and the amendment.');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    setValidationError(null);

    try {
      const job = await createAnalysisJob(originalFile, amendmentFile);
      router.push(`/analyses/${job.id}`);
    } catch (err) {
      setSubmitError(formatApiError(err, UX_MESSAGES.error.createAnalysisFailed));
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await startAnalysis();
  };

  const canSubmit = Boolean(originalFile) && Boolean(amendmentFile) && !isSubmitting;

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 rounded-2xl border border-slate-800 bg-slate-900/20 p-6 sm:p-8"
      aria-busy={isSubmitting}
    >
      <div className="space-y-1">
        <h2 className="text-lg font-bold text-slate-100">Upload documents</h2>
        <p className="text-sm text-slate-400">
          Provide the original agreement and its amendment to start an AI-assisted analysis.
        </p>
      </div>

      {isSubmitting && (
        <LoadingState
          variant="inline"
          message={UX_MESSAGES.loading.upload}
          description="Do not close this page until the upload completes."
        />
      )}

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <FileSlot
          role="ORIGINAL"
          inputId="original-contract-file"
          label="Original contract"
          description="Required"
          file={originalFile}
          disabled={isSubmitting}
          onSelect={handleSelect}
          onClear={handleClear}
        />
        <FileSlot
          role="AMENDMENT"
          inputId="amendment-file"
          label="Amendment"
          description="Required"
          file={amendmentFile}
          disabled={isSubmitting}
          onSelect={handleSelect}
          onClear={handleClear}
        />
      </div>

      <div
        className="flex items-start gap-2.5 rounded-xl border border-amber-500/15 bg-amber-500/5 p-3 text-[11px] leading-relaxed text-amber-400/90"
        role="note"
      >
        <ShieldAlert className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-400" aria-hidden="true" />
        <span>
          Upload PDFs with embedded text or clear image scans of each document
          (PDF, PNG, JPG, WEBP or GIF, up to 20MB). Scanned PDFs without extractable
          text may fail analysis. {UX_MESSAGES.disclaimer}
        </span>
      </div>

      {validationError && (
        <div role="alert" className="rounded-xl border border-rose-500/15 bg-rose-500/5 p-3 text-xs text-rose-400">
          {validationError}
        </div>
      )}

      {submitError && (
        <ErrorState
          title="Upload or analysis start failed"
          message={submitError}
          onRetry={() => void startAnalysis()}
          className="max-w-none py-8"
        />
      )}

      <div className="flex flex-col gap-4 border-t border-slate-800 pt-5 sm:flex-row sm:items-center sm:justify-between">
        <p className="max-w-md text-[11px] leading-relaxed text-slate-500">{UX_MESSAGES.disclaimer}</p>

        <button
          type="submit"
          disabled={!canSubmit}
          aria-disabled={!canSubmit}
          aria-busy={isSubmitting}
          aria-label={isSubmitting ? 'Starting AI-assisted analysis' : 'Start AI-assisted analysis'}
          className={cn(
            'inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3 text-sm font-bold transition-all duration-200',
            canSubmit
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/10 hover:bg-indigo-500 active:scale-[0.98]'
              : 'cursor-not-allowed border border-slate-800 bg-slate-900 text-slate-500 opacity-60'
          )}
        >
          {isSubmitting ? (
            <>Starting analysis…</>
          ) : (
            <>
              <Play className="h-4 w-4 fill-current" aria-hidden="true" />
              Start analysis
            </>
          )}
        </button>
      </div>
    </form>
  );
};
