import type {
  AnalysisSummary,
  AnalysisViewModel,
  FinalAnalysisReport,
  GranularContractChangeOutput,
  LegalChange,
  RiskLevel,
  ValidationBlock,
  ValidationStatus,
} from './types';

export function countHighRiskChanges(changes: LegalChange[]): number {
  return changes.filter((c) => c.risk_level === 'HIGH' || c.risk_level === 'CRITICAL').length;
}

export function emptyViewModel(): AnalysisViewModel {
  return {
    schema_version: '1.0',
    summary: {
      executive_summary: 'No report details returned from the analysis worker.',
      overall_risk_level: 'UNKNOWN',
      total_changes: 0,
      high_risk_changes: 0,
      requires_human_review: false,
    },
    changes: [],
    validation: { status: 'VALID', warnings: [] },
    human_review_recommendations: [],
    key_risks: [],
  };
}

function buildSummaryFromChanges(
  changes: LegalChange[],
  executiveSummary: string,
  overallRiskLevel: RiskLevel
): AnalysisSummary {
  return {
    executive_summary: executiveSummary,
    overall_risk_level: overallRiskLevel,
    total_changes: changes.length,
    high_risk_changes: countHighRiskChanges(changes),
    requires_human_review: changes.some((c) => c.requires_human_review),
  };
}

function buildValidationFromWarnings(warnings: string[]): ValidationBlock {
  const status: ValidationStatus =
    warnings.length > 0 ? 'VALID_WITH_WARNINGS' : 'VALID';
  return { status, warnings };
}

function normalizeV1Report(data: FinalAnalysisReport): AnalysisViewModel {
  const changes = data.changes ?? [];
  const summary = data.analysis_summary ?? buildSummaryFromChanges(changes, '', 'UNKNOWN');

  return {
    schema_version: data.schema_version || '1.0',
    disclaimer: data.disclaimer,
    summary: {
      executive_summary: summary.executive_summary || '',
      overall_risk_level: summary.overall_risk_level || 'UNKNOWN',
      total_changes: summary.total_changes ?? changes.length,
      high_risk_changes: summary.high_risk_changes ?? countHighRiskChanges(changes),
      requires_human_review: summary.requires_human_review ?? changes.some((c) => c.requires_human_review),
    },
    changes,
    validation: data.validation ?? buildValidationFromWarnings([]),
    human_review_recommendations: data.human_review_recommendations ?? [],
    key_risks: Array.isArray(data.risks) ? (data.risks as string[]) : [],
  };
}

function normalizeV2Report(data: GranularContractChangeOutput): AnalysisViewModel {
  const changes = data.changes ?? [];
  const warnings = data.extraction_warnings ?? [];

  return {
    schema_version: data.schema_version || '2.2',
    summary: buildSummaryFromChanges(
      changes,
      data.executive_summary || '',
      data.overall_risk_level || 'UNKNOWN'
    ),
    changes,
    validation: buildValidationFromWarnings(warnings),
    human_review_recommendations: data.human_review_recommendations ?? [],
    key_risks: data.key_risks ?? [],
  };
}

export function normalizeToViewModel(raw: unknown): AnalysisViewModel {
  if (!raw || typeof raw !== 'object') {
    return emptyViewModel();
  }

  const data = raw as FinalAnalysisReport & GranularContractChangeOutput;

  if ('analysis_summary' in data && data.analysis_summary) {
    return normalizeV1Report(data as FinalAnalysisReport);
  }

  return normalizeV2Report(data as GranularContractChangeOutput);
}
