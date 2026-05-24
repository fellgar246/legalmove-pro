"""Shared fixtures for worker-ai tests."""

from typing import Any

from core.extraction_models import (
    GRANULAR_SCHEMA_VERSION,
    GranularContractChangeOutput,
    LegalChange,
    LegalChangeEvidence,
)
from worker import _build_mock_result


def build_mock_result() -> dict[str, Any]:
    return _build_mock_result()


def sample_granular_extraction_output() -> GranularContractChangeOutput:
    return GranularContractChangeOutput(
        schema_version=GRANULAR_SCHEMA_VERSION,
        executive_summary=(
            "The amendment extends payment terms and introduces a liability cap."
        ),
        overall_risk_level="HIGH",
        changes=[
            LegalChange(
                change_id="chg_001",
                change_type="MODIFICATION",
                legal_topic="Payment Terms",
                section_reference="§3 — Payment Terms",
                before_text="Net 30 days.",
                after_text="Net 45 days.",
                summary="Payment deadline extended from 30 to 45 days.",
                risk_level="MEDIUM",
                impact_explanation="Payment timing shifts for the payer.",
                evidence=LegalChangeEvidence(
                    original_quote="Net 30 days.",
                    amendment_quote="Net 45 days.",
                    original_section_reference="§3",
                    amendment_section_reference="§3",
                ),
                confidence="HIGH",
                requires_human_review=False,
            ),
            LegalChange(
                change_id="chg_002",
                change_type="REPLACEMENT",
                legal_topic="Liability",
                section_reference="§7 — Liability",
                before_text="Unlimited liability.",
                after_text="Liability capped at $1M.",
                summary="Liability limitation introduced.",
                risk_level="HIGH",
                impact_explanation="Maximum exposure is now bounded.",
                evidence=LegalChangeEvidence(
                    original_quote="Unlimited liability.",
                    amendment_quote="Liability capped at $1M.",
                ),
                confidence="HIGH",
                requires_human_review=True,
            ),
        ],
        key_risks=["Liability cap introduced"],
        human_review_recommendations=[
            "Review liability cap manually before relying on this report."
        ],
        extraction_warnings=[],
    )


def sample_granular_low_confidence() -> GranularContractChangeOutput:
    return GranularContractChangeOutput(
        schema_version=GRANULAR_SCHEMA_VERSION,
        executive_summary="One change was detected with partial evidence.",
        overall_risk_level="MEDIUM",
        changes=[
            LegalChange(
                change_id="chg_001",
                change_type="MODIFICATION",
                legal_topic="Confidentiality",
                section_reference="§5 — Confidentiality",
                before_text="5 years.",
                after_text=None,
                summary="Confidentiality period may have changed.",
                risk_level="MEDIUM",
                impact_explanation="Retention obligations may differ.",
                evidence=LegalChangeEvidence(original_quote="5 years."),
                confidence="LOW",
                requires_human_review=True,
            )
        ],
        key_risks=[],
        human_review_recommendations=[],
        extraction_warnings=[],
    )
