"""Semantic validation and normalization for granular extraction output (v2.2)."""

from __future__ import annotations

import re

from core.extraction_models import (
    ExtractionConfidenceLiteral,
    GranularContractChangeOutput,
    LegalChange,
    derive_overall_risk_level,
)

CLARIFICATION_IMPACT_SIGNALS = (
    "clarif",
    "does not change",
    "do not change",
    "no change",
    "not alter",
    "not modify",
    "interpret",
    "obligations",
    "non-substantive",
    "non substantive",
)

WARN_EMPTY_CHANGES = (
    "changes is empty but extraction_warnings does not explain why."
)
WARN_EMPTY_EXECUTIVE_SUMMARY = "executive_summary is empty."


def _is_nonempty(value: str | None) -> bool:
    return bool(value and value.strip())


def _normalize_text_for_match(value: str) -> str:
    collapsed = re.sub(r"\s+", " ", value.strip().lower())
    return collapsed


def _quote_supports_text(text: str | None, quote: str | None) -> bool:
    if not _is_nonempty(text):
        return True
    if not _is_nonempty(quote):
        return False
    normalized_text = _normalize_text_for_match(text)  # type: ignore[arg-type]
    normalized_quote = _normalize_text_for_match(quote)  # type: ignore[arg-type]
    return (
        normalized_text in normalized_quote
        or normalized_quote in normalized_text
    )


def _clarification_impact_ok(impact_explanation: str) -> bool:
    if not _is_nonempty(impact_explanation):
        return False
    lowered = impact_explanation.lower()
    return any(signal in lowered for signal in CLARIFICATION_IMPACT_SIGNALS)


def _degrade_confidence(
    current: ExtractionConfidenceLiteral,
    *,
    force_low: bool,
) -> ExtractionConfidenceLiteral:
    if force_low:
        return "LOW"
    return current


def _dedupe_warnings(warnings: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for warning in warnings:
        stripped = warning.strip()
        if stripped and stripped not in seen:
            deduped.append(stripped)
            seen.add(stripped)
    return deduped


def _evidence_quote(evidence: object, field: str) -> str | None:
    if isinstance(evidence, dict):
        value = evidence.get(field)
    else:
        value = getattr(evidence, field, None)
    return value if _is_nonempty(value) else None


def validate_granular_change(change: LegalChange) -> list[str]:
    """Return semantic warnings for a single LegalChange (never raises)."""
    warnings: list[str] = []
    change_id = change.change_id
    has_before = _is_nonempty(change.before_text)
    has_after = _is_nonempty(change.after_text)
    evidence = change.evidence
    original_quote = _evidence_quote(evidence, "original_quote")
    amendment_quote = _evidence_quote(evidence, "amendment_quote")
    has_original_quote = original_quote is not None
    has_amendment_quote = amendment_quote is not None

    if change.is_high_risk() and not _is_nonempty(change.impact_explanation):
        warnings.append(
            f"{change_id}: impact_explanation is required for HIGH or CRITICAL risk."
        )

    if change.change_type == "ADDITION":
        if has_before:
            warnings.append(
                f"{change_id}: ADDITION should not include before_text."
            )
        if not has_after and not has_amendment_quote:
            warnings.append(
                f"{change_id}: ADDITION missing after_text and amendment evidence."
            )
        elif has_after and not has_amendment_quote:
            warnings.append(
                f"{change_id}: ADDITION missing amendment_quote for after_text."
            )

    elif change.change_type == "DELETION":
        if has_after:
            warnings.append(
                f"{change_id}: DELETION should not include after_text."
            )
        if not has_before and not has_original_quote:
            warnings.append(
                f"{change_id}: DELETION missing before_text and original evidence."
            )
        elif has_before and not has_original_quote:
            warnings.append(
                f"{change_id}: DELETION missing original_quote for before_text."
            )

    elif change.change_type in {"MODIFICATION", "REPLACEMENT"}:
        if not has_before or not has_after:
            warnings.append(
                f"{change_id}: {change.change_type} missing before_text and/or after_text."
            )

    elif change.change_type == "CLARIFICATION":
        if not _clarification_impact_ok(change.impact_explanation):
            warnings.append(
                f"{change_id}: CLARIFICATION impact_explanation should clarify "
                "that obligations may not change."
            )

    elif change.change_type == "UNKNOWN":
        if change.confidence == "HIGH":
            warnings.append(
                f"{change_id}: UNKNOWN change_type should not have HIGH confidence."
            )
        if not change.requires_human_review:
            warnings.append(
                f"{change_id}: UNKNOWN change_type requires human review."
            )

    if change.risk_level == "UNKNOWN" and not change.requires_human_review:
        warnings.append(
            f"{change_id}: UNKNOWN risk_level requires human review."
        )

    if not has_original_quote and not has_amendment_quote:
        warnings.append(f"{change_id}: no evidence quotes recorded.")

    has_textual_evidence = (
        has_before
        or has_after
        or has_original_quote
        or has_amendment_quote
    )
    if not has_textual_evidence:
        warnings.append(f"{change_id}: no textual evidence recorded.")

    if (
        has_before
        and has_original_quote
        and not _quote_supports_text(change.before_text, original_quote)
    ):
        warnings.append(
            f"{change_id}: before_text may not be grounded in evidence.original_quote."
        )

    if (
        has_after
        and has_amendment_quote
        and not _quote_supports_text(change.after_text, amendment_quote)
    ):
        warnings.append(
            f"{change_id}: after_text may not be grounded in evidence.amendment_quote."
        )

    return warnings


def validate_granular_output(output: GranularContractChangeOutput) -> list[str]:
    """Return all semantic warnings for a granular extraction output."""
    warnings: list[str] = []
    for change in output.changes:
        warnings.extend(validate_granular_change(change))

    if not output.executive_summary.strip():
        warnings.append(WARN_EMPTY_EXECUTIVE_SUMMARY)

    if not output.changes and not output.extraction_warnings:
        warnings.append(WARN_EMPTY_CHANGES)

    return _dedupe_warnings(warnings)


def apply_change_semantic_coercions(
    change: LegalChange,
    warnings: list[str],
) -> LegalChange:
    """Apply confidence and review coercions based on semantic warnings."""
    confidence = change.confidence
    requires_review = change.requires_human_review

    if warnings:
        confidence = _degrade_confidence(confidence, force_low=True)
        requires_review = True

    if change.change_type == "UNKNOWN":
        if confidence == "HIGH":
            confidence = "MEDIUM"
        requires_review = True

    if change.risk_level == "UNKNOWN":
        requires_review = True

    if change.is_high_risk():
        requires_review = True

    if confidence == "LOW":
        requires_review = True

    return change.model_copy(
        update={
            "confidence": confidence,
            "requires_human_review": requires_review,
            "validation_warnings": warnings,
        }
    )


def normalize_granular_output(
    output: GranularContractChangeOutput,
) -> GranularContractChangeOutput:
    """Validate, coerce, and merge semantic warnings into extraction output."""
    normalized_changes = []
    for change in output.changes:
        change_warnings = validate_granular_change(change)
        normalized_changes.append(
            apply_change_semantic_coercions(change, change_warnings)
        )

    interim = output.model_copy(update={"changes": normalized_changes})
    semantic_warnings = validate_granular_output(interim)
    merged_warnings = _dedupe_warnings(
        list(output.extraction_warnings) + semantic_warnings
    )

    overall = output.overall_risk_level
    if overall == "UNKNOWN" and normalized_changes:
        overall = derive_overall_risk_level(normalized_changes)

    return output.model_copy(
        update={
            "changes": normalized_changes,
            "extraction_warnings": merged_warnings,
            "overall_risk_level": overall,
        }
    )
