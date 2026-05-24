import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agents.extraction_agent import (
    ExtractionAgent,
    _SYSTEM_PROMPT,
    _build_human_message,
)
from core.extraction_models import EXTRACTION_DISCLAIMER
from core.models import (
    DocumentOverview,
    SectionCorrespondenceEntry,
    SectionInventoryEntry,
    StructuralContextMap,
)
from tests.fixtures import sample_granular_extraction_output


def _sample_context_map() -> StructuralContextMap:
    return StructuralContextMap(
        original_overview=DocumentOverview(
            document_type="Services Agreement",
            purpose="Governs provision of consulting services.",
        ),
        amendment_overview=DocumentOverview(
            document_type="Amendment",
            purpose="Modifies payment and liability terms.",
        ),
        original_sections=[
            SectionInventoryEntry(
                identifier="§3",
                title="Payment Terms",
                brief_purpose="Defines payment deadlines.",
            )
        ],
        amendment_sections=[
            SectionInventoryEntry(
                identifier="§3",
                title="Payment Terms",
                brief_purpose="Updates payment deadlines.",
            )
        ],
        section_correspondence=[
            SectionCorrespondenceEntry(
                description="Amendment §3 modifies Original §3 — Payment terms.",
                relationship="modifies",
                amendment_section_ref="§3",
                original_section_ref="§3",
            )
        ],
        amendment_overall_purpose="Adjust payment timing and liability cap.",
    )


def test_system_prompt_includes_disclaimer_and_no_legal_advice():
    assert EXTRACTION_DISCLAIMER in _SYSTEM_PROMPT
    assert "NOT to provide definitive legal advice" in _SYSTEM_PROMPT
    assert "must be signed" in _SYSTEM_PROMPT or "must sign" in _SYSTEM_PROMPT


def test_system_prompt_lists_change_types_and_risk_levels():
    for change_type in (
        "ADDITION",
        "DELETION",
        "MODIFICATION",
        "REPLACEMENT",
        "CLARIFICATION",
        "UNKNOWN",
    ):
        assert change_type in _SYSTEM_PROMPT

    for risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"):
        assert risk_level in _SYSTEM_PROMPT

    assert "Payment Terms" in _SYSTEM_PROMPT
    assert "extraction_warnings" in _SYSTEM_PROMPT


def test_build_human_message_includes_all_three_inputs():
    original = "Original contract paragraph about Net 30 days."
    amendment = "Amendment paragraph about Net 45 days."
    context_map = _sample_context_map()

    message = _build_human_message(original, amendment, context_map)

    assert "## ORIGINAL CONTRACT" in message
    assert original in message
    assert "## AMENDMENT" in message
    assert amendment in message
    assert "## STRUCTURAL CONTEXT MAP" in message
    assert "section_correspondence" in message
    assert "Payment Terms" in message


def test_build_human_message_mentions_extraction_warnings():
    message = _build_human_message("orig", "amend", _sample_context_map())

    assert "extraction_warnings" in message
    assert "schema_version 2.2" in message
    assert "document-level issues" in message


def test_run_with_metadata_validates_parsed_output():
    agent = ExtractionAgent(model="gpt-4o", temperature=0.0)
    granular_output = sample_granular_extraction_output()
    raw_response = MagicMock()
    raw_response.response_metadata = {"model_name": "gpt-4o"}
    raw_response.usage_metadata = {"prompt_tokens": 10, "completion_tokens": 20}

    mock_llm_with_raw = MagicMock()
    mock_llm_with_raw.invoke.return_value = {
        "parsed": granular_output,
        "parsing_error": None,
        "raw": raw_response,
    }
    agent._llm_with_raw = mock_llm_with_raw

    result = agent.run_with_metadata(
        original_text="Original contract text.",
        amendment_text="Amendment text.",
        context_map=_sample_context_map(),
    )

    assert result.output.schema_version == "2.2"
    assert len(result.output.changes) == 2
    assert result.model == "gpt-4o"
    assert result.usage["prompt_tokens"] == 10
    mock_llm_with_raw.invoke.assert_called_once()
