"""Pydantic models for granular legal change extraction (Milestone 2.2)."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator


class ExtractionChangeType(StrEnum):
    ADDITION = "ADDITION"
    DELETION = "DELETION"
    MODIFICATION = "MODIFICATION"
    REPLACEMENT = "REPLACEMENT"
    CLARIFICATION = "CLARIFICATION"
    UNKNOWN = "UNKNOWN"


ExtractionChangeTypeLiteral = Literal[
    "ADDITION",
    "DELETION",
    "MODIFICATION",
    "REPLACEMENT",
    "CLARIFICATION",
    "UNKNOWN",
]


class ExtractionRiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


ExtractionRiskLevelLiteral = Literal["LOW",
                                     "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]


class ExtractionConfidence(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


ExtractionConfidenceLiteral = Literal["LOW", "MEDIUM", "HIGH"]

GRANULAR_SCHEMA_VERSION = "2.2"

HIGH_RISK_LEVELS = frozenset(
    {ExtractionRiskLevel.HIGH, ExtractionRiskLevel.CRITICAL})

EXTRACTION_DISCLAIMER = (
    "AI-generated change extraction for review support only. Not legal advice."
)


def _is_nonempty(value: str | None) -> bool:
    return bool(value and value.strip())


class LegalChangeEvidence(BaseModel):
    """Paired textual evidence from original and amendment documents."""

    original_quote: str | None = None
    amendment_quote: str | None = None
    original_section_reference: str | None = None
    amendment_section_reference: str | None = None
    original_page: int | None = Field(default=None, ge=1)
    amendment_page: int | None = Field(default=None, ge=1)

    def has_textual_evidence(self) -> bool:
        return _is_nonempty(self.original_quote) or _is_nonempty(self.amendment_quote)


class LegalChange(BaseModel):
    change_id: str = Field(min_length=1)
    change_type: ExtractionChangeTypeLiteral
    legal_topic: str = Field(min_length=1)
    section_reference: str = Field(min_length=1)
    before_text: str | None = None
    after_text: str | None = None
    summary: str = Field(min_length=1)
    risk_level: ExtractionRiskLevelLiteral
    impact_explanation: str = ""
    evidence: LegalChangeEvidence = Field(default_factory=LegalChangeEvidence)
    confidence: ExtractionConfidenceLiteral
    requires_human_review: bool = True

    validation_warnings: list[str] = Field(default_factory=list, exclude=True)

    def has_textual_evidence(self) -> bool:
        return (
            _is_nonempty(self.before_text)
            or _is_nonempty(self.after_text)
            or self.evidence.has_textual_evidence()
        )

    def is_high_risk(self) -> bool:
        return self.risk_level in {"HIGH", "CRITICAL"}

    def needs_review(self) -> bool:
        return (
            self.requires_human_review
            or self.confidence == "LOW"
            or self.is_high_risk()
        )

    @field_validator("change_id", "legal_topic", "section_reference", "summary")
    @classmethod
    def strip_required_strings(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Required string fields must not be blank.")
        return stripped

    @model_validator(mode="after")
    def apply_soft_rules(self) -> Self:
        if self.is_high_risk() and not _is_nonempty(self.impact_explanation):
            raise ValueError(
                "impact_explanation is required when risk_level is HIGH or CRITICAL."
            )

        from core.granular_validation import (
            apply_change_semantic_coercions,
            validate_granular_change,
        )

        warnings = validate_granular_change(self)
        coerced = apply_change_semantic_coercions(self, warnings)
        object.__setattr__(self, "validation_warnings", warnings)
        object.__setattr__(self, "confidence", coerced.confidence)
        object.__setattr__(self, "requires_human_review", coerced.requires_human_review)
        return self


class GranularContractChangeOutput(BaseModel):
    schema_version: str = GRANULAR_SCHEMA_VERSION
    executive_summary: str
    overall_risk_level: ExtractionRiskLevelLiteral = "UNKNOWN"
    changes: list[LegalChange] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    human_review_recommendations: list[str] = Field(default_factory=list)
    extraction_warnings: list[str] = Field(default_factory=list)

    @field_validator("executive_summary")
    @classmethod
    def executive_summary_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("executive_summary must not be blank.")
        return stripped

    @model_validator(mode="after")
    def validate_output_consistency(self) -> Self:
        rolled_warnings = list(self.extraction_warnings)

        for change in self.changes:
            rolled_warnings.extend(change.validation_warnings)

        if not self.changes and not rolled_warnings:
            raise ValueError(
                "changes may be empty only when extraction_warnings explains why."
            )

        overall = self.overall_risk_level
        if overall == "UNKNOWN" and self.changes:
            overall = derive_overall_risk_level(self.changes)

        object.__setattr__(self, "extraction_warnings", rolled_warnings)
        object.__setattr__(self, "overall_risk_level", overall)
        return self


def derive_overall_risk_level(
    changes: list[LegalChange],
) -> ExtractionRiskLevelLiteral:
    rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3, "UNKNOWN": 1}
    max_change = max(
        changes, key=lambda change: rank.get(change.risk_level, 1))
    level = max_change.risk_level
    if level == "CRITICAL":
        return "CRITICAL"
    if level == "UNKNOWN":
        return "MEDIUM"
    return level  # type: ignore[return-value]


GranularLegalChange = LegalChange


class TextEvidenceItem(BaseModel):
    """Deprecated — use LegalChangeEvidence."""

    source_document: Literal["ORIGINAL", "AMENDMENT"]
    quote: str
    location_hint: str | None = None
