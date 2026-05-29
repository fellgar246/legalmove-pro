export type DocumentRole = 'ORIGINAL' | 'AMENDMENT';

export interface UploadedDocument {
  id: string;
  filename: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  document_role: DocumentRole;
  status: string;
  created_at: string;
}

export type AnalysisStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'NEEDS_REVIEW';

export interface AnalysisJob {
  id: string;
  original_document_id: string;
  original_filename?: string;
  amendment_document_id: string;
  amendment_filename?: string;
  status: AnalysisStatus;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';

export type ValidationStatus = 'VALID' | 'INVALID' | 'VALID_WITH_WARNINGS';

export interface LegalChangeEvidence {
  original_quote?: string | null;
  amendment_quote?: string | null;
  original_section_reference?: string | null;
  amendment_section_reference?: string | null;
  original_page?: number | null;
  amendment_page?: number | null;
}

export interface LegalChange {
  change_id: string;
  change_type: 'ADDITION' | 'DELETION' | 'MODIFICATION' | 'REPLACEMENT' | 'CLARIFICATION' | 'UNKNOWN';
  legal_topic: string;
  section_reference: string;
  before_text?: string | null;
  after_text?: string | null;
  summary: string;
  risk_level: RiskLevel;
  impact_explanation?: string;
  evidence?: LegalChangeEvidence;
  confidence: 'LOW' | 'MEDIUM' | 'HIGH';
  requires_human_review: boolean;
}

// Milestone 2.1 Pydantic Model Representation
export interface AnalysisSummary {
  executive_summary: string;
  overall_risk_level: RiskLevel;
  total_changes: number;
  high_risk_changes: number;
  requires_human_review: boolean;
}

export interface ValidationBlock {
  status: ValidationStatus;
  warnings: string[];
}

export interface FinalAnalysisReport {
  schema_version: string;
  disclaimer: string;
  analysis_summary: AnalysisSummary;
  changes: LegalChange[];
  risks?: string[] | any[];
  human_review_recommendations?: string[];
  validation: ValidationBlock;
}

// Milestone 2.2 Granular Contract Change Output Pydantic Model Representation
// Since result can hold either schema v1.0 or v2.2, we represent both under FinalAnalysisReport
export interface GranularContractChangeOutput {
  schema_version: string;
  executive_summary: string;
  overall_risk_level: RiskLevel;
  changes: LegalChange[];
  key_risks?: string[];
  human_review_recommendations?: string[];
  extraction_warnings?: string[];
}

export interface AnalysisViewModel {
  schema_version: string;
  disclaimer?: string;
  summary: AnalysisSummary;
  changes: LegalChange[];
  validation: ValidationBlock;
  human_review_recommendations: string[];
  key_risks: string[];
}

export interface AnalysisResultResponse {
  analysis_job_id: string;
  schema_version: string;
  validation_status: string; // "VALID", "INVALID", etc.
  created_at: string;
  result: GranularContractChangeOutput | FinalAnalysisReport;
}
