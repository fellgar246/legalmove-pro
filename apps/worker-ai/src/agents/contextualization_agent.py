"""
Agent 1 — Contextualization.

Responsibility: take the original contract and amendment plaintexts and produce a
structured context map describing:
  - Which sections exist in each document and how they align.
  - The high-level purpose of each structural block.
  - Structural differences (new, removed, or renamed sections).

This agent does NOT extract substantive content changes; it only builds context
so Agent 2 can extract changes accurately.
"""

from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.models import StructuralContextMap
from core.validation_utils import ensure_no_structured_output_error
from infra.http_config import load_openai_runtime_config
from infra.openai_errors import maybe_wrap_context_limit_error

_SYSTEM_PROMPT = """\
You are a senior legal analyst specializing in contract structure analysis.

You analyze two texts — an original contract and its amendment — and fill
the structured context map (JSON schema) provided by the tool. Every field
must reflect only STRUCTURE and ALIGNMENT between documents:

- original_overview / amendment_overview: document type and high-level purpose.
- original_sections / amendment_sections: exhaustive inventory; for each item
  use the visible identifier, title (or short label), and one-sentence purpose.
  Do not describe wording deltas here.
- section_correspondence: one row per meaningful link. Use relationship:
  modifies | adds_new | removes | renames_or_restructures | unchanged_reference.
  Use amendment_section_ref and original_section_ref to cite section labels.
  For purely new amendment-only sections, original_section_ref may be null.
- amendment_overall_purpose: one paragraph on why the amendment exists and its
  scope — no specific redline details, no old/new values.

Do NOT list or analyze substantive text changes; the next agent does that.
Be exhaustive with inventories and correspondence rows when the documents are long.
"""


@dataclass(frozen=True)
class ContextualizationResult:
    """Agent output plus token/model usage metadata."""

    context_map: StructuralContextMap
    model: str | None
    usage: dict[str, Any]


def _extract_response_metadata(response: Any) -> tuple[str | None, dict[str, Any]]:
    """Extract model name and token usage from a LangChain/OpenAI response object."""
    response_metadata = getattr(response, "response_metadata", {}) or {}
    usage_metadata = getattr(response, "usage_metadata", None)
    usage = usage_metadata or response_metadata.get("token_usage") or {}
    model = response_metadata.get("model_name") or response_metadata.get("model")
    return model, dict(usage)


class ContextualizationAgent:
    """
    Contract-structure contextualization agent.

    Analyzes both documents and returns a Pydantic-validated structural context map
    that Agent 2 consumes for change extraction.
    """

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.0) -> None:
        rtc = load_openai_runtime_config()
        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            timeout=rtc.timeout,
            max_retries=rtc.max_retries,
        )
        self._llm = llm.with_structured_output(StructuralContextMap)
        self._llm_with_raw = llm.with_structured_output(
            StructuralContextMap,
            include_raw=True,
        )

    def run(
        self,
        original_text: str,
        amendment_text: str,
    ) -> StructuralContextMap:
        """
        Build the structural context map from the two OCR'd texts.

        Args:
            original_text: Full plaintext of the original contract (from Vision OCR).
            amendment_text: Full plaintext of the amendment (from Vision OCR).

        Returns:
            Validated StructuralContextMap.
        """
        human_content = (
            "## ORIGINAL CONTRACT\n\n"
            f"{original_text}\n\n"
            "---\n\n"
            "## AMENDMENT\n\n"
            f"{amendment_text}\n\n"
            "---\n\n"
            "Populate every field of the structural context map per your instructions."
        )

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=human_content),
        ]

        try:
            result: StructuralContextMap = self._llm.invoke(messages)
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
    ) -> ContextualizationResult:
        """Run contextualization and preserve token/model metadata from the LLM call."""
        human_content = (
            "## ORIGINAL CONTRACT\n\n"
            f"{original_text}\n\n"
            "---\n\n"
            "## AMENDMENT\n\n"
            f"{amendment_text}\n\n"
            "---\n\n"
            "Populate every field of the structural context map per your instructions."
        )

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=human_content),
        ]

        try:
            result = self._llm_with_raw.invoke(messages)
        except Exception as exc:
            wrapped = maybe_wrap_context_limit_error(exc)
            if wrapped is not None:
                raise wrapped from exc
            raise
        ensure_no_structured_output_error(
            "ContextualizationAgent",
            result.get("parsing_error"),
        )

        parsed: StructuralContextMap = StructuralContextMap.model_validate(
            result["parsed"].model_dump()
        )
        raw_response = result.get("raw")
        model, usage = _extract_response_metadata(raw_response)
        return ContextualizationResult(
            context_map=parsed,
            model=model,
            usage=usage,
        )
