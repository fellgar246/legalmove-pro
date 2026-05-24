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
)
from core.models import ContractChangeOutput
from pipeline.result_mapper import (
    DEFAULT_TOPIC,
    EMPTY_SUMMARY,
    RECOMMENDATION_LOW_CONFIDENCE,
    RECOMMENDATION_MANUAL_REVIEW,
    RECOMMENDATION_NOT_LEGAL_ADVICE,
    WARN_DUPLICATE_CHANGE_IDS,
    WARN_EMPTY_EXECUTIVE_SUMMARY,
    WARN_EMPTY_SUMMARY,
    WARN_LEGACY_MAPPING,
    WARN_NO_SECTIONS,
    WARN_NO_TEXT_EVIDENCE,
    WARN_NO_TOPICS,
    WARN_UNRECOGNIZED_OUTPUT,
    map_contract_change_output_to_final_report,
    map_contract_change_to_report,
    map_extraction_to_final_report,
)


def test_maps_one_change_per_section_from_pydantic():
    output = ContractChangeOutput(
        sections_changed=["§3 — Payment Terms", "§7 — Liability"],
        topics_touched=["Payment Terms", "Liability"],
        summary_of_the_change="The amendment extends payment terms and caps liability.",
    )

    report = map_contract_change_output_to_final_report(output)

    assert report["schema_version"] == "1.0"
    assert report["disclaimer"] == "AI-generated review support. Not legal advice."
    assert report["analysis_summary"]["executive_summary"] == output.summary_of_the_change
    assert report["analysis_summary"]["total_changes"] == 2
    assert report["analysis_summary"]["overall_risk_level"] == "MEDIUM"
    assert report["analysis_summary"]["high_risk_changes"] == 0
    assert report["analysis_summary"]["requires_human_review"] is True
    assert len(report["changes"]) == 2

    first, second = report["changes"]
    assert first["change_id"] == "chg_001"
    assert first["change_type"] == "MODIFICATION"
    assert first["legal_topic"] == "Payment Terms"
    assert first["section_reference"] == "§3 — Payment Terms"
    assert first["before_text"] is None
    assert first["after_text"] is None
    assert first["summary"] == output.summary_of_the_change
    assert first["risk_level"] == "MEDIUM"
    assert first["requires_human_review"] is True

    assert second["change_id"] == "chg_002"
    assert second["legal_topic"] == "Liability"
    assert second["section_reference"] == "§7 — Liability"

    assert report["risks"] == []
    assert report["validation"]["status"] == "VALID_WITH_WARNINGS"
    assert WARN_NO_TEXT_EVIDENCE in report["validation"]["warnings"]
    assert WARN_LEGACY_MAPPING in report["validation"]["warnings"]
    assert RECOMMENDATION_MANUAL_REVIEW in report["human_review_recommendations"]
    assert RECOMMENDATION_NOT_LEGAL_ADVICE in report["human_review_recommendations"]


def test_accepts_dict_input():
    raw = {
        "sections_changed": ["Clause 3"],
        "topics_touched": [],
        "summary_of_the_change": "Payment terms updated.",
    }

    report = map_contract_change_output_to_final_report(raw)

    assert report["analysis_summary"]["total_changes"] == 1
    assert report["changes"][0]["legal_topic"] == DEFAULT_TOPIC
    assert WARN_NO_TOPICS in report["validation"]["warnings"]


def test_empty_output_produces_no_changes():
    output = ContractChangeOutput(
        sections_changed=[],
        topics_touched=[],
        summary_of_the_change="",
    )

    report = map_contract_change_output_to_final_report(output)

    assert report["analysis_summary"]["executive_summary"] == EMPTY_SUMMARY
    assert report["analysis_summary"]["total_changes"] == 0
    assert report["changes"] == []
    assert report["validation"]["status"] == "VALID_WITH_WARNINGS"
    assert WARN_NO_SECTIONS in report["validation"]["warnings"]
    assert WARN_NO_TOPICS in report["validation"]["warnings"]
    assert WARN_EMPTY_SUMMARY in report["validation"]["warnings"]
    assert WARN_NO_TEXT_EVIDENCE in report["validation"]["warnings"]


def test_summary_only_without_sections_has_no_changes_and_warnings():
    output = ContractChangeOutput(
        sections_changed=[],
        topics_touched=["Confidentiality"],
        summary_of_the_change="Confidentiality obligations were tightened.",
    )

    report = map_contract_change_output_to_final_report(output)

    assert report["analysis_summary"]["total_changes"] == 0
    assert report["changes"] == []
    assert WARN_NO_SECTIONS in report["validation"]["warnings"]


def test_backward_compatible_alias():
    output = ContractChangeOutput(
        sections_changed=["§1"],
        topics_touched=["Terms"],
        summary_of_the_change="Updated terms.",
    )

    assert map_contract_change_to_report(output) == map_contract_change_output_to_final_report(output)


def _granular_change(**overrides) -> LegalChange:
    payload = {
        "change_id": "chg_001",
        "change_type": "MODIFICATION",
        "legal_topic": "Payment Terms",
        "section_reference": "§3 — Payment Terms",
        "before_text": "Net 30 days.",
        "after_text": "Net 45 days.",
        "summary": "Payment deadline extended.",
        "risk_level": "MEDIUM",
        "impact_explanation": "Cash flow timing may shift.",
        "evidence": {
            "original_quote": "Net 30 days.",
            "amendment_quote": "Net 45 days.",
        },
        "confidence": "HIGH",
        "requires_human_review": False,
    }
    payload.update(overrides)
    return LegalChange.model_validate(payload)


def _granular_output(**overrides) -> GranularContractChangeOutput:
    payload = {
        "schema_version": GRANULAR_SCHEMA_VERSION,
        "executive_summary": "Payment terms were extended.",
        "overall_risk_level": "MEDIUM",
        "changes": [_granular_change()],
        "key_risks": [],
        "human_review_recommendations": [],
        "extraction_warnings": [],
    }
    payload.update(overrides)
    return GranularContractChangeOutput.model_validate(payload)


def test_granular_maps_changes_with_evidence():
    output = _granular_output(
        changes=[
            _granular_change(),
            _granular_change(
                change_id="chg_002",
                legal_topic="Liability",
                section_reference="§7 — Liability",
                before_text="Unlimited liability.",
                after_text="Liability capped at $1M.",
                summary="Liability cap introduced.",
                risk_level="CRITICAL",
                impact_explanation="Exposure is now bounded.",
                evidence={
                    "original_quote": "Unlimited liability.",
                    "amendment_quote": "Liability capped at $1M.",
                },
                confidence="HIGH",
            ),
        ],
        overall_risk_level="CRITICAL",
        key_risks=["Liability cap introduced"],
    )

    report = map_extraction_to_final_report(output)

    assert report["analysis_summary"]["executive_summary"] == output.executive_summary
    assert report["analysis_summary"]["total_changes"] == 2
    assert report["analysis_summary"]["high_risk_changes"] == 1
    assert report["analysis_summary"]["overall_risk_level"] == "HIGH"
    assert report["validation"]["status"] == "VALID"
    assert WARN_NO_TEXT_EVIDENCE not in report["validation"]["warnings"]
    assert report["risks"] == ["Liability cap introduced"]

    first = report["changes"][0]
    assert first["before_text"] == "Net 30 days."
    assert first["after_text"] == "Net 45 days."
    assert "Impact: Cash flow timing may shift." in first["summary"]
    assert first["impact_explanation"] == "Cash flow timing may shift."
    assert first["confidence"] == "HIGH"
    assert first["evidence"]["original_quote"] == "Net 30 days."
    assert first["evidence"]["amendment_quote"] == "Net 45 days."

    second = report["changes"][1]
    assert second["risk_level"] == "HIGH"
    assert second["impact_explanation"] == "Exposure is now bounded."
    assert second["confidence"] == "HIGH"


def test_granular_low_confidence_yields_valid_with_warnings():
    output = _granular_output(
        executive_summary="One uncertain change detected.",
        changes=[
            _granular_change(
                before_text=None,
                after_text="Net 45 days.",
                evidence={"amendment_quote": "Net 45 days."},
                confidence="MEDIUM",
                requires_human_review=False,
            )
        ],
    )

    report = map_extraction_to_final_report(output)

    assert report["validation"]["status"] == "VALID_WITH_WARNINGS"
    assert any("missing before_text" in warning for warning in report["validation"]["warnings"])
    assert RECOMMENDATION_LOW_CONFIDENCE in report["human_review_recommendations"]
    assert report["changes"][0]["requires_human_review"] is True


def test_granular_clarification_maps_to_modification():
    output = _granular_output(
        changes=[
            _granular_change(
                change_type="CLARIFICATION",
                summary="Clarifies payment timing language.",
            )
        ]
    )

    report = map_extraction_to_final_report(output)
    assert report["changes"][0]["change_type"] == "MODIFICATION"


def test_granular_addition_with_before_text_soft_warning():
    output = _granular_output(
        changes=[
            _granular_change(
                change_type="ADDITION",
                before_text="Forbidden.",
                after_text="New clause.",
                evidence={"amendment_quote": "New clause."},
            )
        ]
    )

    report = map_extraction_to_final_report(output)
    assert report["validation"]["status"] == "VALID_WITH_WARNINGS"
    assert any("ADDITION should not include before_text" in warning for warning in report["validation"]["warnings"])


def test_granular_empty_changes_with_extraction_warnings():
    output = GranularContractChangeOutput.model_validate(
        {
            "executive_summary": "No substantive changes were detected.",
            "changes": [],
            "extraction_warnings": [
                "No atomic changes extracted; amendment may be administrative only."
            ],
        }
    )

    report = map_extraction_to_final_report(output)

    assert report["analysis_summary"]["total_changes"] == 0
    assert report["validation"]["status"] == "VALID_WITH_WARNINGS"
    assert "No atomic changes extracted" in report["validation"]["warnings"][0]


def test_granular_regenerates_duplicate_change_ids():
    output = _granular_output(
        executive_summary="Duplicate ids present.",
        changes=[
            _granular_change(change_id="chg_dup"),
            _granular_change(change_id="chg_dup", section_reference="§4"),
        ],
    )

    report = map_extraction_to_final_report(output)

    change_ids = [change["change_id"] for change in report["changes"]]
    assert len(set(change_ids)) == 2
    assert WARN_DUPLICATE_CHANGE_IDS in report["validation"]["warnings"]


def test_granular_without_evidence_yields_valid_with_warnings():
    output = _granular_output(
        executive_summary="One change lacks textual evidence.",
        changes=[
            _granular_change(
                before_text=None,
                after_text=None,
                evidence={},
                confidence="MEDIUM",
            )
        ],
    )

    report = map_extraction_to_final_report(output)

    assert report["validation"]["status"] == "VALID_WITH_WARNINGS"
    assert report["changes"][0]["confidence"] == "LOW"
    assert report["changes"][0]["requires_human_review"] is True
    assert report["changes"][0]["evidence"] == {
        "original_quote": None,
        "amendment_quote": None,
        "original_section_reference": None,
        "amendment_section_reference": None,
        "original_page": None,
        "amendment_page": None,
    }


def test_invalid_dict_returns_invalid_report():
    report = map_extraction_to_final_report({"foo": "bar"})

    assert report["validation"]["status"] == "INVALID"
    assert report["changes"] == []
    assert report["risks"] == []
    assert WARN_UNRECOGNIZED_OUTPUT in report["validation"]["warnings"]


def test_granular_empty_executive_summary_returns_invalid():
    output = GranularContractChangeOutput.model_construct(
        schema_version=GRANULAR_SCHEMA_VERSION,
        executive_summary="",
        overall_risk_level="MEDIUM",
        changes=[_granular_change()],
        key_risks=[],
        human_review_recommendations=[],
        extraction_warnings=[],
    )

    report = map_extraction_to_final_report(output)

    assert report["validation"]["status"] == "INVALID"
    assert report["changes"] == []
    assert WARN_EMPTY_EXECUTIVE_SUMMARY in report["validation"]["warnings"]
