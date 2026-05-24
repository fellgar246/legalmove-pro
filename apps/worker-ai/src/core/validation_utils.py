"""
Clear messages for Pydantic validation and structured output failures.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError


def format_pydantic_validation_error(err: ValidationError) -> str:
    """Summarize field errors from a ValidationError for stderr / logs."""
    parts: list[str] = []
    for item in err.errors():
        loc = " → ".join(str(x) for x in item.get("loc", ()))
        msg = item.get("msg", "")
        parts.append(f"  • {loc}: {msg}" if loc else f"  • {msg}")
    return "\n".join(parts) if parts else str(err)


def structured_output_failure_message(agent_label: str, parsing_error: Any) -> str:
    """Build the user-facing message when LangChain reports parsing_error on structured output."""
    if isinstance(parsing_error, ValidationError):
        body = format_pydantic_validation_error(parsing_error)
        return f"[{agent_label}] Output does not match the Pydantic schema:\n{body}"
    cause = getattr(parsing_error, "__cause__", None)
    if isinstance(cause, ValidationError):
        body = format_pydantic_validation_error(cause)
        return f"[{agent_label}] Output does not match the Pydantic schema:\n{body}"
    return f"[{agent_label}] Structured output parsing failed: {parsing_error!s}"


def ensure_no_structured_output_error(agent_label: str, parsing_error: Any | None) -> None:
    if parsing_error:
        raise ValueError(structured_output_failure_message(agent_label, parsing_error))
