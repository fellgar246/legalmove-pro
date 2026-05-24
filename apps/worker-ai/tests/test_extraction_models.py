import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.extraction_models import (
    GRANULAR_SCHEMA_VERSION,
    GranularContractChangeOutput,
    LegalChange,
    LegalChangeEvidence,
    derive_overall_risk_level,
)
from core.models import ContractChangeOutput


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
            "original_section_reference": "§3",
            "amendment_section_reference": "§3",
        },
        "confidence": "HIGH",
        "requires_human_review": False,
    }
    payload.update(overrides)
    return payload


def test_modification_valid_full_evidence():
    change = LegalChange.model_validate(_base_change())
    assert change.change_type == "MODIFICATION"
    assert change.confidence == "HIGH"
    assert change.validation_warnings == []


def test_addition_missing_after_text_soft_warning():
    change = LegalChange.model_validate(
        _base_change(
            change_type="ADDITION",
            before_text=None,
            after_text=None,
            evidence={"original_quote": None, "amendment_quote": None},
        )
    )
    assert change.confidence == "LOW"
    assert change.requires_human_review is True
    assert any("ADDITION missing after_text" in warning for warning in change.validation_warnings)


def test_deletion_missing_before_text_soft_warning():
    change = LegalChange.model_validate(
        _base_change(
            change_type="DELETION",
            before_text=None,
            after_text=None,
            evidence={"original_quote": None, "amendment_quote": None},
        )
    )
    assert change.confidence == "LOW"
    assert any("DELETION missing before_text" in warning for warning in change.validation_warnings)


def test_modification_missing_before_or_after_soft_warning():
    change = LegalChange.model_validate(
        _base_change(
            before_text=None,
            after_text="Net 45 days.",
            evidence={"original_quote": None, "amendment_quote": "Net 45 days."},
        )
    )
    assert change.confidence == "LOW"
    assert any("missing before_text and/or after_text" in warning for warning in change.validation_warnings)


def test_high_risk_requires_impact_explanation_hard_fail():
    with pytest.raises(ValidationError, match="impact_explanation"):
        LegalChange.model_validate(
            _base_change(risk_level="HIGH", impact_explanation="")
        )


def test_critical_risk_requires_impact_explanation_hard_fail():
    with pytest.raises(ValidationError, match="impact_explanation"):
        LegalChange.model_validate(
            _base_change(risk_level="CRITICAL", impact_explanation="   ")
        )


def test_empty_changes_without_warnings_hard_fail():
    with pytest.raises(ValidationError, match="extraction_warnings explains why"):
        GranularContractChangeOutput.model_validate(
            {
                "executive_summary": "No changes found.",
                "changes": [],
                "extraction_warnings": [],
            }
        )


def test_empty_changes_with_warnings_valid():
    output = GranularContractChangeOutput.model_validate(
        {
            "executive_summary": "No substantive changes were detected.",
            "changes": [],
            "extraction_warnings": [
                "No atomic changes extracted; amendment may be administrative only."
            ],
        }
    )
    assert output.changes == []
    assert len(output.extraction_warnings) == 1


def test_requires_human_review_coerced_on_low_confidence():
    change = LegalChange.model_validate(
        _base_change(
            before_text=None,
            confidence="MEDIUM",
            requires_human_review=False,
        )
    )
    assert change.confidence == "LOW"
    assert change.requires_human_review is True


def test_requires_human_review_coerced_on_high_risk():
    change = LegalChange.model_validate(
        _base_change(
            risk_level="HIGH",
            impact_explanation="Exposure increases materially.",
            confidence="HIGH",
            requires_human_review=False,
        )
    )
    assert change.requires_human_review is True
    assert change.needs_review() is True


def test_legal_change_evidence_has_textual_evidence():
    evidence = LegalChangeEvidence(original_quote="Original clause.")
    assert evidence.has_textual_evidence() is True

    empty = LegalChangeEvidence()
    assert empty.has_textual_evidence() is False


def test_legal_change_is_high_risk_and_needs_review():
    change = LegalChange.model_validate(
        _base_change(risk_level="CRITICAL", impact_explanation="Severe exposure shift.")
    )
    assert change.is_high_risk() is True
    assert change.needs_review() is True


def test_overall_risk_derived_from_changes_when_unknown():
    changes = [
        LegalChange.model_validate(_base_change(risk_level="LOW")),
        LegalChange.model_validate(
            _base_change(
                change_id="chg_002",
                risk_level="CRITICAL",
                impact_explanation="Critical liability exposure.",
            )
        ),
    ]
    assert derive_overall_risk_level(changes) == "CRITICAL"


def test_warnings_rollup_to_extraction_warnings():
    output = GranularContractChangeOutput.model_validate(
        {
            "executive_summary": "One uncertain change detected.",
            "changes": [
                _base_change(
                    before_text=None,
                    after_text=None,
                    evidence={"original_quote": None, "amendment_quote": None},
                )
            ],
            "extraction_warnings": ["Root-level warning."],
        }
    )
    assert "Root-level warning." in output.extraction_warnings
    assert any("missing before_text" in warning for warning in output.extraction_warnings)


def test_granular_output_defaults_schema_version():
    output = GranularContractChangeOutput(
        executive_summary="Two changes identified.",
        changes=[LegalChange.model_validate(_base_change())],
    )
    assert output.schema_version == GRANULAR_SCHEMA_VERSION


def test_legacy_contract_change_output_still_validates():
    legacy = ContractChangeOutput(
        sections_changed=["§3"],
        topics_touched=["Payment Terms"],
        summary_of_the_change="Payment terms updated.",
    )
    assert legacy.sections_changed == ["§3"]
