import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.extraction_models import (
    GRANULAR_SCHEMA_VERSION,
    GranularContractChangeOutput,
    LegalChange,
)
from core.granular_validation import (
    WARN_EMPTY_CHANGES,
    WARN_EMPTY_EXECUTIVE_SUMMARY,
    normalize_granular_output,
    validate_granular_change,
    validate_granular_output,
)
from pipeline.result_mapper import map_extraction_to_final_report


def _base_change(**overrides) -> dict:
    payload = {
        "change_id": "chg_001",
        "change_type": "MODIFICATION",
        "legal_topic": "Payment Terms",
        "section_reference": "§3 — Payment Terms",
        "before_text": "Net 30 days.",
        "after_text": "Net 45 days.",
        "summary": "Payment deadline extended.",
        "risk_level": "MEDIUM",
        "impact_explanation": "Cash flow timing may shift for the payer.",
        "evidence": {
            "original_quote": "Net 30 days.",
            "amendment_quote": "Net 45 days.",
        },
        "confidence": "HIGH",
        "requires_human_review": False,
    }
    payload.update(overrides)
    return payload


def test_addition_missing_after_text():
    change = LegalChange.model_validate(
        _base_change(
            change_type="ADDITION",
            before_text=None,
            after_text=None,
            evidence={"original_quote": None, "amendment_quote": None},
        )
    )
    warnings = validate_granular_change(change)
    assert any("ADDITION missing after_text" in warning for warning in warnings)


def test_deletion_with_after_text():
    change = LegalChange.model_validate(
        _base_change(
            change_type="DELETION",
            before_text="Removed clause.",
            after_text="Still here.",
            evidence={
                "original_quote": "Removed clause.",
                "amendment_quote": None,
            },
        )
    )
    warnings = validate_granular_change(change)
    assert any("DELETION should not include after_text" in warning for warning in warnings)


def test_clarification_missing_impact():
    change = LegalChange.model_validate(
        _base_change(
            change_type="CLARIFICATION",
            impact_explanation="",
        )
    )
    warnings = validate_granular_change(change)
    assert any(
        "CLARIFICATION impact_explanation should clarify" in warning
        for warning in warnings
    )


def test_clarification_valid_impact():
    change = LegalChange.model_validate(
        _base_change(
            change_type="CLARIFICATION",
            impact_explanation="Clarifies wording without changing obligations.",
        )
    )
    warnings = validate_granular_change(change)
    assert not any("CLARIFICATION impact_explanation" in warning for warning in warnings)


def test_unknown_change_high_confidence_degraded():
    raw_change = LegalChange.model_construct(
        **_base_change(
            change_type="UNKNOWN",
            confidence="HIGH",
            requires_human_review=False,
        )
    )
    warnings = validate_granular_change(raw_change)
    assert any(
        "UNKNOWN change_type should not have HIGH confidence" in warning
        for warning in warnings
    )

    output = GranularContractChangeOutput.model_construct(
        executive_summary="Uncertain change detected.",
        changes=[raw_change],
    )
    normalized = normalize_granular_output(output)
    assert normalized.changes[0].confidence == "LOW"
    assert normalized.changes[0].requires_human_review is True


def test_unknown_risk_requires_review():
    raw_change = LegalChange.model_construct(
        **_base_change(
            risk_level="UNKNOWN",
            requires_human_review=False,
        )
    )
    warnings = validate_granular_change(raw_change)
    assert any(
        "UNKNOWN risk_level requires human review" in warning
        for warning in warnings
    )

    output = GranularContractChangeOutput.model_construct(
        executive_summary="Risk classification uncertain.",
        changes=[raw_change],
    )
    normalized = normalize_granular_output(output)
    assert normalized.changes[0].requires_human_review is True


def test_no_evidence_quotes_warning():
    change = LegalChange.model_validate(
        _base_change(
            before_text=None,
            after_text=None,
            evidence={"original_quote": None, "amendment_quote": None},
        )
    )
    warnings = validate_granular_change(change)
    assert any("no evidence quotes recorded" in warning for warning in warnings)


def test_ungrounded_before_text():
    change = LegalChange.model_validate(
        _base_change(
            before_text="Invented clause language.",
            evidence={
                "original_quote": "Net 30 days.",
                "amendment_quote": "Net 45 days.",
            },
        )
    )
    warnings = validate_granular_change(change)
    assert any(
        "before_text may not be grounded in evidence.original_quote" in warning
        for warning in warnings
    )


def test_ungrounded_after_text():
    change = LegalChange.model_validate(
        _base_change(
            after_text="Fabricated after language.",
            evidence={
                "original_quote": "Net 30 days.",
                "amendment_quote": "Net 45 days.",
            },
        )
    )
    warnings = validate_granular_change(change)
    assert any(
        "after_text may not be grounded in evidence.amendment_quote" in warning
        for warning in warnings
    )


def test_empty_changes_without_explanation():
    output = GranularContractChangeOutput.model_construct(
        schema_version=GRANULAR_SCHEMA_VERSION,
        executive_summary="No changes found.",
        changes=[],
        extraction_warnings=[],
    )
    warnings = validate_granular_output(output)
    assert WARN_EMPTY_CHANGES in warnings


def test_empty_executive_summary_warning():
    output = GranularContractChangeOutput.model_construct(
        schema_version=GRANULAR_SCHEMA_VERSION,
        executive_summary="",
        changes=[LegalChange.model_validate(_base_change())],
        extraction_warnings=[],
    )
    warnings = validate_granular_output(output)
    assert WARN_EMPTY_EXECUTIVE_SUMMARY in warnings


def test_normalize_merges_warnings_into_extraction_warnings():
    change = LegalChange.model_validate(
        _base_change(
            before_text=None,
            after_text="Net 45 days.",
            evidence={"original_quote": None, "amendment_quote": "Net 45 days."},
            confidence="HIGH",
        )
    )
    output = GranularContractChangeOutput(
        executive_summary="One uncertain change detected.",
        changes=[change],
        extraction_warnings=["Root-level warning."],
    )
    normalized = normalize_granular_output(output)
    assert "Root-level warning." in normalized.extraction_warnings
    assert any("missing before_text" in warning for warning in normalized.extraction_warnings)
    assert normalized.changes[0].confidence == "LOW"


def test_mapper_coerce_applies_normalize():
    raw = {
        "schema_version": GRANULAR_SCHEMA_VERSION,
        "executive_summary": "One uncertain change detected.",
        "overall_risk_level": "MEDIUM",
        "changes": [
            _base_change(
                before_text=None,
                after_text="Net 45 days.",
                evidence={"original_quote": None, "amendment_quote": "Net 45 days."},
                confidence="MEDIUM",
                requires_human_review=False,
            )
        ],
        "key_risks": [],
        "human_review_recommendations": [],
        "extraction_warnings": [],
    }

    report = map_extraction_to_final_report(raw)

    assert report["validation"]["status"] == "VALID_WITH_WARNINGS"
    assert any("missing before_text" in warning for warning in report["validation"]["warnings"])
    assert report["changes"][0]["requires_human_review"] is True
