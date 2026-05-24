"""Pydantic models for FinalAnalysisReport v1 stored in analysis_results."""

from typing import Literal

from pydantic import BaseModel, Field

DISCLAIMER = "AI-generated review support. Not legal advice."

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
ChangeType = Literal["MODIFICATION", "ADDITION", "DELETION", "REPLACEMENT"]
ValidationStatus = Literal["VALID", "INVALID", "VALID_WITH_WARNINGS"]


class AnalysisSummary(BaseModel):
    executive_summary: str
    overall_risk_level: RiskLevel
    total_changes: int
    high_risk_changes: int
    requires_human_review: bool


class DetectedChangeItem(BaseModel):
    change_id: str
    change_type: ChangeType
    legal_topic: str | None = None
    section_reference: str | None = None
    before_text: str | None = None
    after_text: str | None = None
    summary: str
    risk_level: RiskLevel
    requires_human_review: bool = True


class ValidationBlock(BaseModel):
    status: ValidationStatus
    warnings: list[str] = Field(default_factory=list)


class FinalAnalysisReport(BaseModel):
    schema_version: str = "1.0"
    disclaimer: str = DISCLAIMER
    analysis_summary: AnalysisSummary
    changes: list[DetectedChangeItem]
    risks: list = Field(default_factory=list)
    human_review_recommendations: list[str] = Field(default_factory=list)
    validation: ValidationBlock
