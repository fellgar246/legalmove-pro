"""Map extraction output (granular or legacy) to FinalAnalysisReport v1."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from core.extraction_models import (
    ExtractionChangeTypeLiteral,
    ExtractionRiskLevelLiteral,
    GranularContractChangeOutput,
    LegalChange,
)
from core.granular_validation import normalize_granular_output
from core.models import ContractChangeOutput
from core.report_models import (
    DISCLAIMER,
    AnalysisSummary,
    ChangeType,
    DetectedChangeItem,
    FinalAnalysisReport,
    RiskLevel,
    ValidationBlock,
    ValidationStatus,
)

DEFAULT_TOPIC = "General Contract Change"
EMPTY_SUMMARY = "No substantive changes were detected in the amendment analysis."
INVALID_EXECUTIVE_SUMMARY = "Analysis report could not be generated from the extraction output."

RECOMMENDATION_MANUAL_REVIEW = (
    "Review all detected changes manually before relying on this report."
)
RECOMMENDATION_NOT_LEGAL_ADVICE = "This AI-generated output is not legal advice."
RECOMMENDATION_LOW_CONFIDENCE = (
    "Prioritize manual review for changes flagged with low extraction confidence."
)

WARN_NO_SECTIONS = "No sections_changed were identified in the extraction output."
WARN_NO_TOPICS = "No topics_touched were identified in the extraction output."
WARN_EMPTY_SUMMARY = "summary_of_the_change is empty."
WARN_NO_TEXT_EVIDENCE = (
    "The original extraction output does not include textual before/after evidence."
)
WARN_DUPLICATE_CHANGE_IDS = "Duplicate change_id values were regenerated during mapping."
WARN_LEGACY_MAPPING = (
    "Legacy extraction output used; no per-change textual evidence available."
)
WARN_UNRECOGNIZED_OUTPUT = "Unrecognized extraction output shape."
WARN_EMPTY_EXECUTIVE_SUMMARY = "executive_summary is empty."

# Backward-compatible aliases used by older tests and imports.
PIPELINE_V1_WARNING = WARN_NO_TEXT_EVIDENCE
NO_SECTIONS_WARNING = WARN_NO_SECTIONS
GENERIC_REVIEW = RECOMMENDATION_MANUAL_REVIEW
WARN_EMPTY_GRANULAR_CHANGES = (
    "Granular extraction returned no changes; verify the amendment scope manually."
)

_RISK_RANK: dict[RiskLevel, int] = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def _is_granular_payload(raw: Any) -> bool:
    if isinstance(raw, GranularContractChangeOutput):
        return True
    if isinstance(raw, dict):
        if "sections_changed" in raw:
            return False
        schema_version = str(raw.get("schema_version", ""))
        if schema_version.startswith("2."):
            return True
        if "changes" in raw:
            return True
    return False


def _coerce_extraction_output(
    raw_output: Any,
) -> GranularContractChangeOutput | ContractChangeOutput:
    if isinstance(raw_output, GranularContractChangeOutput):
        return normalize_granular_output(raw_output)
    if isinstance(raw_output, ContractChangeOutput):
        return raw_output
    if isinstance(raw_output, dict):
        if _is_granular_payload(raw_output):
            validated = GranularContractChangeOutput.model_validate(raw_output)
            return normalize_granular_output(validated)
        if "sections_changed" in raw_output or "summary_of_the_change" in raw_output:
            return ContractChangeOutput.model_validate(raw_output)
        raise TypeError(WARN_UNRECOGNIZED_OUTPUT)
    raise TypeError(
        "raw_output must be a GranularContractChangeOutput, ContractChangeOutput, "
        "or a compatible dict"
    )


def _build_invalid_report(warnings: list[str]) -> dict:
    report = FinalAnalysisReport(
        disclaimer=DISCLAIMER,
        analysis_summary=AnalysisSummary(
            executive_summary=INVALID_EXECUTIVE_SUMMARY,
            overall_risk_level="MEDIUM",
            total_changes=0,
            high_risk_changes=0,
            requires_human_review=True,
        ),
        changes=[],
        risks=[],
        human_review_recommendations=[
            RECOMMENDATION_MANUAL_REVIEW,
            RECOMMENDATION_NOT_LEGAL_ADVICE,
        ],
        validation=ValidationBlock(
            status="INVALID",
            warnings=warnings,
        ),
    )
    return report.model_dump()


def _enrich_change_dict(change: LegalChange, mapped: dict[str, Any]) -> dict[str, Any]:
    mapped["impact_explanation"] = change.impact_explanation or None
    mapped["confidence"] = change.confidence
    mapped["evidence"] = change.evidence.model_dump()
    return mapped


def _resolve_validation_status(
    *,
    executive_summary: str,
    changes_count: int,
    warnings: list[str],
    has_low_confidence: bool,
    has_missing_evidence: bool,
) -> ValidationStatus:
    if not executive_summary.strip():
        return "INVALID"
    if warnings or has_low_confidence or has_missing_evidence:
        return "VALID_WITH_WARNINGS"
    if changes_count == 0:
        return "VALID_WITH_WARNINGS"
    return "VALID"


def _topic_for_index(topics_touched: list[str], index: int) -> str:
    if index < len(topics_touched) and topics_touched[index].strip():
        return topics_touched[index].strip()
    return DEFAULT_TOPIC


def _change_summary(section_reference: str, summary_of_the_change: str) -> str:
    if summary_of_the_change.strip():
        return summary_of_the_change
    return f"Changes detected in {section_reference}."


def _build_legacy_changes(output: ContractChangeOutput) -> list[DetectedChangeItem]:
    changes: list[DetectedChangeItem] = []
    for index, section in enumerate(output.sections_changed):
        section_reference = section.strip()
        if not section_reference:
            continue
        changes.append(
            DetectedChangeItem(
                change_id=f"chg_{index + 1:03d}",
                change_type="MODIFICATION",
                legal_topic=_topic_for_index(output.topics_touched, index),
                section_reference=section_reference,
                before_text=None,
                after_text=None,
                summary=_change_summary(section_reference, output.summary_of_the_change),
                risk_level="MEDIUM",
                requires_human_review=True,
            )
        )
    return changes


def _build_legacy_warnings(output: ContractChangeOutput) -> list[str]:
    warnings: list[str] = [WARN_NO_TEXT_EVIDENCE, WARN_LEGACY_MAPPING]
    if not output.sections_changed:
        warnings.append(WARN_NO_SECTIONS)
    if not output.topics_touched:
        warnings.append(WARN_NO_TOPICS)
    if not output.summary_of_the_change.strip():
        warnings.append(WARN_EMPTY_SUMMARY)
    return warnings


def _legacy_executive_summary(output: ContractChangeOutput) -> str:
    if output.summary_of_the_change.strip():
        return output.summary_of_the_change
    if output.sections_changed:
        sections = ", ".join(output.sections_changed)
        return f"Changes were identified in the following sections: {sections}."
    return EMPTY_SUMMARY


def _map_legacy_to_report(output: ContractChangeOutput) -> dict:
    changes = _build_legacy_changes(output)
    warnings = _build_legacy_warnings(output)
    executive_summary = _legacy_executive_summary(output)
    report = FinalAnalysisReport(
        disclaimer=DISCLAIMER,
        analysis_summary=AnalysisSummary(
            executive_summary=executive_summary,
            overall_risk_level="MEDIUM",
            total_changes=len(changes),
            high_risk_changes=0,
            requires_human_review=True,
        ),
        changes=changes,
        risks=[],
        human_review_recommendations=[
            RECOMMENDATION_MANUAL_REVIEW,
            RECOMMENDATION_NOT_LEGAL_ADVICE,
        ],
        validation=ValidationBlock(
            status=_resolve_validation_status(
                executive_summary=executive_summary,
                changes_count=len(changes),
                warnings=warnings,
                has_low_confidence=False,
                has_missing_evidence=False,
            ),
            warnings=warnings,
        ),
    )
    return report.model_dump()


def _normalize_change_type(change_type: ExtractionChangeTypeLiteral) -> ChangeType:
    if change_type in {"ADDITION", "DELETION", "MODIFICATION", "REPLACEMENT"}:
        return change_type  # type: ignore[return-value]
    return "MODIFICATION"


def _normalize_risk_level(risk_level: ExtractionRiskLevelLiteral) -> RiskLevel:
    if risk_level == "CRITICAL":
        return "HIGH"
    if risk_level == "UNKNOWN":
        return "MEDIUM"
    if risk_level in {"LOW", "MEDIUM", "HIGH"}:
        return risk_level  # type: ignore[return-value]
    return "MEDIUM"


def _normalize_overall_risk_level(risk_level: ExtractionRiskLevelLiteral) -> RiskLevel:
    if risk_level == "CRITICAL":
        return "HIGH"
    if risk_level == "UNKNOWN":
        return "MEDIUM"
    if risk_level in {"LOW", "MEDIUM", "HIGH"}:
        return risk_level  # type: ignore[return-value]
    return "MEDIUM"


def _build_granular_summary(change: LegalChange) -> str:
    summary = change.summary.strip()
    impact = change.impact_explanation.strip()
    if impact and impact not in summary:
        if summary:
            return f"{summary}\n\nImpact: {impact}"
        return f"Impact: {impact}"
    return summary or "No summary provided."


def _normalize_change_ids(
    changes: list[LegalChange],
) -> tuple[list[tuple[LegalChange, str]], bool]:
    seen: set[str] = set()
    duplicates = False
    normalized: list[tuple[LegalChange, str]] = []
    for index, change in enumerate(changes):
        requested = change.change_id.strip() or f"chg_{index + 1:03d}"
        change_id = requested
        if change_id in seen:
            duplicates = True
            change_id = f"chg_{index + 1:03d}"
        if change_id in seen:
            duplicates = True
            suffix = 2
            while f"{change_id}_r{suffix}" in seen:
                suffix += 1
            change_id = f"{change_id}_r{suffix}"
        seen.add(change_id)
        normalized.append((change, change_id))
    return normalized, duplicates


def _build_granular_detected_changes(
    normalized: list[tuple[LegalChange, str]],
) -> list[DetectedChangeItem]:
    detected: list[DetectedChangeItem] = []
    for change, change_id in normalized:
        detected.append(
            DetectedChangeItem(
                change_id=change_id,
                change_type=_normalize_change_type(change.change_type),
                legal_topic=change.legal_topic,
                section_reference=change.section_reference,
                before_text=change.before_text,
                after_text=change.after_text,
                summary=_build_granular_summary(change),
                risk_level=_normalize_risk_level(change.risk_level),
                requires_human_review=change.needs_review(),
            )
        )
    return detected


def _merge_recommendations(output: GranularContractChangeOutput) -> list[str]:
    recommendations: list[str] = []
    seen: set[str] = set()

    for item in [
        *output.human_review_recommendations,
        RECOMMENDATION_MANUAL_REVIEW,
        RECOMMENDATION_NOT_LEGAL_ADVICE,
    ]:
        stripped = item.strip()
        if stripped and stripped not in seen:
            recommendations.append(stripped)
            seen.add(stripped)

    if any(change.confidence == "LOW" for change in output.changes):
        if RECOMMENDATION_LOW_CONFIDENCE not in seen:
            recommendations.append(RECOMMENDATION_LOW_CONFIDENCE)

    return recommendations


def _build_mapper_warnings(
    output: GranularContractChangeOutput,
    *,
    duplicate_ids: bool,
) -> list[str]:
    warnings = list(output.extraction_warnings)
    if duplicate_ids:
        warnings.append(WARN_DUPLICATE_CHANGE_IDS)
    return warnings


def _map_granular_to_report(output: GranularContractChangeOutput) -> dict:
    executive_summary = output.executive_summary.strip()
    if not executive_summary:
        return _build_invalid_report([WARN_EMPTY_EXECUTIVE_SUMMARY])

    normalized, duplicate_ids = _normalize_change_ids(output.changes)
    changes = _build_granular_detected_changes(normalized)
    warnings = _build_mapper_warnings(output, duplicate_ids=duplicate_ids)

    has_low_confidence = any(change.confidence == "LOW" for change in output.changes)
    has_missing_evidence = any(
        not change.has_textual_evidence() for change in output.changes
    )

    high_risk_changes = sum(
        1 for change in output.changes if change.risk_level in {"HIGH", "CRITICAL"}
    )
    requires_human_review = any(change.needs_review() for change in output.changes)

    validation_status = _resolve_validation_status(
        executive_summary=executive_summary,
        changes_count=len(changes),
        warnings=warnings,
        has_low_confidence=has_low_confidence,
        has_missing_evidence=has_missing_evidence,
    )

    report = FinalAnalysisReport(
        disclaimer=DISCLAIMER,
        analysis_summary=AnalysisSummary(
            executive_summary=executive_summary,
            overall_risk_level=_normalize_overall_risk_level(output.overall_risk_level),
            total_changes=len(changes),
            high_risk_changes=high_risk_changes,
            requires_human_review=requires_human_review,
        ),
        changes=changes,
        risks=list(output.key_risks),
        human_review_recommendations=_merge_recommendations(output),
        validation=ValidationBlock(
            status=validation_status,
            warnings=warnings,
        ),
    )
    report_dict = report.model_dump()
    for mapped_change, (source_change, _change_id) in zip(
        report_dict["changes"], normalized
    ):
        _enrich_change_dict(source_change, mapped_change)
    return report_dict


def map_extraction_to_final_report(raw_output: Any) -> dict:
    """
    Transform granular or legacy extraction output into FinalAnalysisReport v1.

    Pure function: no OpenAI, no DB, no worker dependencies.
    """
    try:
        coerced = _coerce_extraction_output(raw_output)
    except (TypeError, ValidationError) as exc:
        message = str(exc).strip() or WARN_UNRECOGNIZED_OUTPUT
        return _build_invalid_report([message])

    if isinstance(coerced, GranularContractChangeOutput):
        return _map_granular_to_report(coerced)
    return _map_legacy_to_report(coerced)


def map_contract_change_output_to_final_report(raw_output: Any) -> dict:
    """Backward-compatible alias for map_extraction_to_final_report."""
    return map_extraction_to_final_report(raw_output)


def map_contract_change_to_report(raw_output: Any) -> dict:
    """Backward-compatible alias for map_extraction_to_final_report."""
    return map_extraction_to_final_report(raw_output)
