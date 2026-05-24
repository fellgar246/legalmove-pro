"""
Agent 2 — Change extraction.

Responsibility: using the typed structural context map (`StructuralContextMap`)
from Agent 1 plus both full document texts, identify, isolate, and precisely describe
every atomic legal change introduced by the amendment.

The result is a GranularContractChangeOutput (schema v2.2) validated by Pydantic,
produced via OpenAI structured outputs.
"""

from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.extraction_models import EXTRACTION_DISCLAIMER, GranularContractChangeOutput
from core.models import StructuralContextMap
from core.validation_utils import ensure_no_structured_output_error
from infra.http_config import load_openai_runtime_config
from infra.openai_errors import maybe_wrap_context_limit_error

_ROLE_AND_SCOPE = """\
You are a senior legal analyst specializing in contract change extraction.

Your role is to support human review — NOT to provide definitive legal advice.
Use neutral, review-support language. Never tell the reader what they must sign,
reject, or conclude legally.
"""

_INPUTS_DESCRIPTION = """\
You will receive:
  1. The full text of the ORIGINAL CONTRACT (OCR/plaintext).
  2. The full text of the AMENDMENT (OCR/plaintext).
  3. A STRUCTURAL CONTEXT MAP (validated JSON from a prior step) with section
     inventories, pairwise correspondence, and amendment purpose.

Use the context map to align sections, but always prefer literal document text
when extracting quotes and evidence.
"""

_OUTPUT_SCHEMA_HINT = """\
Produce GranularContractChangeOutput with schema_version "2.2".

Root fields:
  - executive_summary
  - overall_risk_level
  - changes[]
  - key_risks[]
  - human_review_recommendations[]
  - extraction_warnings[]

Each item in changes[] must include:
  change_id, change_type, legal_topic, section_reference,
  before_text, after_text, summary, risk_level, impact_explanation,
  evidence, confidence, requires_human_review.

The evidence object is paired:
  original_quote, amendment_quote,
  original_section_reference, amendment_section_reference,
  original_page, amendment_page (when visible in the source text).
"""

_NON_NEGOTIABLE_RULES = """\
NON-NEGOTIABLE RULES:
1. Do NOT provide definitive legal advice.
2. Use ONLY the text provided — no external law, no assumptions.
3. Do NOT invent clauses, dates, amounts, parties, or obligations.
4. If evidence is insufficient, set confidence = LOW and requires_human_review = true.
5. Include textual evidence in evidence.*_quote whenever possible.
6. before_text must come from the ORIGINAL CONTRACT only.
7. after_text must come from the AMENDMENT only.
8. If a clause is new, before_text must be null.
9. If a clause was removed, after_text must be null.
10. If change_type cannot be determined confidently, use UNKNOWN.
11. If there is potentially relevant risk, set requires_human_review = true.
12. Avoid conclusions such as "this is illegal" or "must be signed".
13. Use human-review support language (e.g. "may affect", "appears to", "consider reviewing").
14. Emit ONE object in changes[] per atomic legal change (not one per section label).
15. When risk_level is HIGH or CRITICAL, impact_explanation must be non-empty.
16. before_text, after_text, and evidence quotes must be literal copies from the
    source documents. Use null when unavailable. Never paraphrase as a quote.
"""

_CHANGE_TYPE_GUIDE = """\
CHANGE TYPE GUIDE:
- ADDITION: new clause or provision added (before_text = null).
- DELETION: clause or provision removed (after_text = null).
- MODIFICATION: partial change within an existing clause.
- REPLACEMENT: entire clause or block substantively substituted.
- CLARIFICATION: text clarifies without materially changing obligations.
- UNKNOWN: classification not possible with available evidence.
"""

_LEGAL_TOPICS = """\
SUGGESTED legal_topic values (use closest match or "General Contract Change"):
Payment Terms, Liability, Confidentiality, Termination, Governing Law,
Jurisdiction, Term, Renewal, Scope of Services, Deliverables, Intellectual Property,
Data Protection, Penalties, Warranties, Indemnification, Force Majeure,
General Contract Change.
"""

_RISK_LEVEL_GUIDE = """\
RISK LEVEL GUIDE (preliminary review signal only):
- LOW: minor or clarifying change.
- MEDIUM: relevant change worth reviewing.
- HIGH: affects obligations, payments, liability, penalties, term, jurisdiction,
  or other important rights.
- CRITICAL: may severely affect legal or economic exposure.
- UNKNOWN: insufficient evidence to assess risk confidently.
"""

_CONFIDENCE_AND_REVIEW = """\
CONFIDENCE AND HUMAN REVIEW:
- Set confidence = LOW when OCR seems incomplete, sections are misaligned,
  evidence is partial, change_type = UNKNOWN, or the structural map conflicts with text.
- LOW confidence must set requires_human_review = true.
- requires_human_review = true by default; set false only when confidence = HIGH
  and evidence is complete for that change.
- HIGH or CRITICAL risk_level should normally set requires_human_review = true.
"""

_EXTRACTION_WARNINGS_GUIDE = """\
Populate extraction_warnings[] at the root level when you detect document-wide issues:
- OCR text appears incomplete, garbled, or truncated.
- Sections in the structural map are not comparable to visible document text.
- Changes are ambiguous and cannot be tied to clear evidence.
- Textual evidence is missing for multiple changes.
- The structural context map conflicts with the literal document text.

If changes[] is empty, extraction_warnings must explain why.
"""

_SYSTEM_PROMPT = "\n\n".join(
    [
        _ROLE_AND_SCOPE,
        _INPUTS_DESCRIPTION,
        _OUTPUT_SCHEMA_HINT,
        _NON_NEGOTIABLE_RULES,
        _CHANGE_TYPE_GUIDE,
        _LEGAL_TOPICS,
        _RISK_LEVEL_GUIDE,
        _CONFIDENCE_AND_REVIEW,
        _EXTRACTION_WARNINGS_GUIDE,
        f'Disclaimer: "{EXTRACTION_DISCLAIMER}"',
        "Output ONLY the structured JSON. Do not add explanations outside the schema.",
    ]
)


def _build_human_message(
    original_text: str,
    amendment_text: str,
    context_map: StructuralContextMap,
) -> str:
    """Build the user message with original, amendment, and structural context."""
    map_json = context_map.model_dump_json(indent=2)
    return (
        "## TASK\n"
        "Extract every atomic legal change between the ORIGINAL CONTRACT and the AMENDMENT.\n"
        "Use the STRUCTURAL CONTEXT MAP to align sections, but prefer literal document text.\n"
        "If the map conflicts with visible text, note it in extraction_warnings and "
        "reduce confidence on affected changes.\n\n"
        "## ORIGINAL CONTRACT\n\n"
        f"{original_text}\n\n"
        "---\n\n"
        "## AMENDMENT\n\n"
        f"{amendment_text}\n\n"
        "---\n\n"
        "## STRUCTURAL CONTEXT MAP (validated JSON)\n\n"
        f"{map_json}\n\n"
        "---\n\n"
        "## OUTPUT INSTRUCTIONS\n"
        "- Populate GranularContractChangeOutput with schema_version 2.2.\n"
        "- Emit one changes[] item per atomic legal change.\n"
        "- Populate key_risks and human_review_recommendations for human reviewers.\n"
        "- Populate extraction_warnings for document-level issues (OCR, alignment, ambiguity).\n"
        "- If no substantive changes exist, leave changes[] empty and explain in "
        "extraction_warnings.\n"
    )


@dataclass(frozen=True)
class ExtractionResult:
    """Structured agent output plus token/model usage metadata."""

    output: GranularContractChangeOutput
    model: str | None
    usage: dict[str, Any]


def _extract_response_metadata(response: Any) -> tuple[str | None, dict[str, Any]]:
    """Extract model name and token usage from a raw LangChain/OpenAI response object."""
    response_metadata = getattr(response, "response_metadata", {}) or {}
    usage_metadata = getattr(response, "usage_metadata", None)
    usage = usage_metadata or response_metadata.get("token_usage") or {}
    model = response_metadata.get("model_name") or response_metadata.get("model")
    return model, dict(usage)


class ExtractionAgent:
    """
    Amendment change-extraction agent.

    Uses OpenAI structured outputs so results are always valid
    GranularContractChangeOutput instances without manual JSON parsing steps.
    """

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.0) -> None:
        rtc = load_openai_runtime_config()
        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            timeout=rtc.timeout,
            max_retries=rtc.max_retries,
        )
        self._llm = llm.with_structured_output(GranularContractChangeOutput)
        self._llm_with_raw = llm.with_structured_output(
            GranularContractChangeOutput,
            include_raw=True,
        )

    def run(
        self,
        original_text: str,
        amendment_text: str,
        context_map: StructuralContextMap,
    ) -> GranularContractChangeOutput:
        """
        Extract and structure all changes between the original contract and the amendment.

        Args:
            original_text: Full plaintext of the original contract.
            amendment_text: Full plaintext of the amendment.
            context_map: Validated structural map from ContextualizationAgent.

        Returns:
            Pydantic-validated GranularContractChangeOutput with granular changes.
        """
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(
                content=_build_human_message(original_text, amendment_text, context_map)
            ),
        ]

        try:
            result: GranularContractChangeOutput = self._llm.invoke(messages)
        except Exception as exc:
            wrapped = maybe_wrap_context_limit_error(exc)
            if wrapped is not None:
                raise wrapped from exc
            raise
        return result

    def run_with_metadata(
        self,
        original_text: str,
        amendment_text: str,
        context_map: StructuralContextMap,
    ) -> ExtractionResult:
        """
        Extract changes and preserve token/model metadata from the LLM call.
        """
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(
                content=_build_human_message(original_text, amendment_text, context_map)
            ),
        ]

        try:
            result = self._llm_with_raw.invoke(messages)
        except Exception as exc:
            wrapped = maybe_wrap_context_limit_error(exc)
            if wrapped is not None:
                raise wrapped from exc
            raise
        ensure_no_structured_output_error(
            "ExtractionAgent",
            result.get("parsing_error"),
        )

        parsed: GranularContractChangeOutput = GranularContractChangeOutput.model_validate(
            result["parsed"].model_dump()
        )
        raw_response = result.get("raw")
        model, usage = _extract_response_metadata(raw_response)
        return ExtractionResult(output=parsed, model=model, usage=usage)
