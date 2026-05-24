"""
Pydantic models for the LegalMove contract-comparison pipeline.

Defines validated schemas emitted by the multi-agent workflow.
"""

from typing import List, Literal

from pydantic import BaseModel, Field


class DocumentOverview(BaseModel):
    """High-level document classification and stated purpose."""

    document_type: str = Field(
        description=(
            "Instrument type (e.g. services agreement, NDA, commercial lease)."
        )
    )
    purpose: str = Field(
        description="Primary commercial or legal purpose in one or two sentences."
    )


class SectionInventoryEntry(BaseModel):
    """A labeled section entry in the structural inventory."""

    identifier: str = Field(
        description='Visible textual reference (e.g. "§3", "Clause 7", "Article 12").'
    )
    title: str = Field(
        description="Section heading if present; otherwise a short descriptive label."
    )
    brief_purpose: str = Field(
        description="Single-sentence explanation of scope without listing redline deltas."
    )


class SectionCorrespondenceEntry(BaseModel):
    """Links amendment sections to counterparts in the original contract."""

    description: str = Field(
        description=(
            "Clear sentence bridging both sides "
            '(e.g. "Amendment §3 modifies Original §4 — Payment terms").'
        )
    )
    relationship: Literal[
        "modifies",
        "adds_new",
        "removes",
        "renames_or_restructures",
        "unchanged_reference",
    ] = Field(
        description=(
            "modifies: amendment alters an existing section; "
            "adds_new: new section/content introduced in the amendment; "
            "removes: original content eliminated or superseded by the amendment; "
            "renames_or_restructures: same substantive topic reorganized or renamed; "
            "unchanged_reference: cited or reaffirmed without material change."
        )
    )
    amendment_section_ref: str = Field(
        description='Identifier of the AMENDMENT section (e.g. "§2.1").'
    )
    original_section_ref: str | None = Field(
        default=None,
        description=(
            "Identifier of the affected or related ORIGINAL section; "
            "null when the row describes purely amendment-only novelty."
        ),
    )


class StructuralContextMap(BaseModel):
    """
    Structural alignment between original contract and amendment.

    Produced by the contextualization agent; does not enumerate substantive wording
    changes (that is the extraction agent's job).
    """

    original_overview: DocumentOverview
    amendment_overview: DocumentOverview
    original_sections: List[SectionInventoryEntry] = Field(
        description="Ordered inventory of relevant sections detected in the original."
    )
    amendment_sections: List[SectionInventoryEntry] = Field(
        description="Ordered inventory of relevant sections detected in the amendment."
    )
    section_correspondence: List[SectionCorrespondenceEntry] = Field(
        description=(
            "How amendment sections relate to the original material; "
            "include rows for new, removed, or reorganized portions."
        )
    )
    amendment_overall_purpose: str = Field(
        description=(
            "Single paragraph explaining why the amendment exists and its general scope. "
            "Avoid enumerating granular text swaps or substituted numeric amounts."
        )
    )


class ContractChangeOutput(BaseModel):
    """
    Structured output describing changes between an original agreement and amendment.

    Attributes:
        sections_changed: Labels for materially modified sections
            (e.g. "§3 — Payment Terms").
        topics_touched: Commercial or legal topic categories impacted
            (e.g. "Liability", "Confidentiality").
        summary_of_the_change: Narrative detailing every substantive change driven
            by the amendment.
    """

    sections_changed: List[str] = Field(
        description="Identifiers of contract sections amended by the amendment."
    )
    topics_touched: List[str] = Field(
        description="Commercial/legal topic categories materially impacted."
    )
    summary_of_the_change: str = Field(
        description="Detailed narrative summarizing substantive amendment revisions."
    )
