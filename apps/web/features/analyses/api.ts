import { apiClient } from '@/lib/api-client';
import { 
  DocumentRole, 
  UploadedDocument, 
  AnalysisStatus, 
  AnalysisJob, 
  AnalysisResultResponse,
  GranularContractChangeOutput,
  FinalAnalysisReport
} from './types';

// localStorage registry key
const TRACKED_JOBS_KEY = 'legalmove_tracked_jobs';

interface TrackedJob {
  id: string;
  original_filename: string;
  amendment_filename: string;
  created_at: string;
}

function getTrackedJobs(): TrackedJob[] {
  if (typeof window === 'undefined') return [];
  try {
    const data = localStorage.getItem(TRACKED_JOBS_KEY);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error('Error reading tracked jobs from localStorage', error);
    return [];
  }
}

function addTrackedJob(job: TrackedJob): void {
  if (typeof window === 'undefined') return;
  try {
    const jobs = getTrackedJobs();
    if (jobs.some((j) => j.id === job.id)) return;
    localStorage.setItem(TRACKED_JOBS_KEY, JSON.stringify([job, ...jobs]));
  } catch (error) {
    console.error('Error writing tracked job to localStorage', error);
  }
}

function removeTrackedJob(id: string): void {
  if (typeof window === 'undefined') return;
  try {
    const jobs = getTrackedJobs();
    localStorage.setItem(TRACKED_JOBS_KEY, JSON.stringify(jobs.filter((j) => j.id !== id)));
  } catch (error) {
    console.error('Error removing tracked job from localStorage', error);
  }
}

/**
 * 1. Uploads a contract document (PDF) to the Go API
 * POST /documents (multipart/form-data)
 */
export async function uploadDocument(file: File, role: DocumentRole): Promise<UploadedDocument> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_role', role);

  return apiClient.postFormData<UploadedDocument>('/documents', formData);
}

/**
 * 2. Creates a contract analysis job on the Go API
 * POST /analyses (JSON)
 */
export async function createAnalysis(
  originalDocumentId: string,
  amendmentDocumentId: string
): Promise<AnalysisJob> {
  return apiClient.postJson<AnalysisJob>('/analyses', {
    original_document_id: originalDocumentId,
    amendment_document_id: amendmentDocumentId,
  });
}

/**
 * 3. Retrieves analysis metadata/status by Job ID
 * GET /analyses/:id
 */
export async function getAnalysis(id: string): Promise<AnalysisJob> {
  return apiClient.get<AnalysisJob>(`/analyses/${id}`);
}

/**
 * 4. Retrieves the final analysis result containing changes and summary reports
 * GET /analyses/:id/result
 */
export async function getAnalysisResult(id: string): Promise<AnalysisResultResponse> {
  return apiClient.get<AnalysisResultResponse>(`/analyses/${id}/result`);
}

/**
 * 5. Dashboard Helper: Reads tracked localStorage Job IDs and fetches status details
 * from the live Go API in parallel.
 */
export async function getAnalyses(): Promise<AnalysisJob[]> {
  const tracked = getTrackedJobs();
  if (tracked.length === 0) return [];

  // Parallel status retrieval
  const results = await Promise.allSettled(
    tracked.map(async (item) => {
      try {
        const liveJob = await getAnalysis(item.id);
        return {
          ...liveJob,
          original_filename: item.original_filename,
          amendment_filename: item.amendment_filename,
        };
      } catch (err: any) {
        // Fallback for offline API or reset database items
        return {
          id: item.id,
          original_document_id: '',
          original_filename: item.original_filename,
          amendment_document_id: '',
          amendment_filename: item.amendment_filename,
          status: 'FAILED' as AnalysisStatus,
          error_message: err.message || 'Cannot retrieve status from Go API',
          started_at: null,
          completed_at: null,
          created_at: item.created_at,
          updated_at: item.created_at,
        } as AnalysisJob;
      }
    })
  );

  return results.map((r, index) => {
    if (r.status === 'fulfilled') {
      return r.value;
    }
    // Fallback if promise rejected outright
    const item = tracked[index];
    return {
      id: item.id,
      original_document_id: '',
      original_filename: item.original_filename,
      amendment_document_id: '',
      amendment_filename: item.amendment_filename,
      status: 'FAILED' as AnalysisStatus,
      error_message: 'API server connection timeout',
      started_at: null,
      completed_at: null,
      created_at: item.created_at,
      updated_at: item.created_at,
    } as AnalysisJob;
  });
}

/**
 * 6. Deletes an analysis job from browser history registry
 */
export async function deleteAnalysis(id: string): Promise<boolean> {
  removeTrackedJob(id);
  return true;
}

/**
 * 7. Combined Orchestration: Uploads both documents and launches the analysis pipeline
 * Used sequentially by the upload form component
 */
export async function createAnalysisJob(
  originalFile: File,
  amendmentFile: File
): Promise<AnalysisJob> {
  // 1. Upload original document
  const originalDoc = await uploadDocument(originalFile, 'ORIGINAL');

  // 2. Upload amendment document
  const amendmentDoc = await uploadDocument(amendmentFile, 'AMENDMENT');

  // 3. Initiate analysis job
  const liveJob = await createAnalysis(originalDoc.id, amendmentDoc.id);

  // 4. Save job info to browser registry for tracking
  addTrackedJob({
    id: liveJob.id,
    original_filename: originalFile.name,
    amendment_filename: amendmentFile.name,
    created_at: new Date().toISOString(),
  });

  return {
    ...liveJob,
    original_filename: originalFile.name,
    amendment_filename: amendmentFile.name,
  };
}
