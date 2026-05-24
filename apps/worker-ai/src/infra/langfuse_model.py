"""OpenAI model id normalization for Langfuse cost attribution."""

from __future__ import annotations

import re

# OpenAI returns dated snapshots (e.g. gpt-4o-2024-08-06); Langfuse pricing rows
# are usually keyed by the base name (gpt-4o).
_OPENAI_DATED_SNAPSHOT = re.compile(r"^(.+)-\d{4}-\d{2}-\d{2}$")


def normalize_openai_model_for_langfuse(
    api_model: str | None, *, fallback: str = "gpt-4o"
) -> str:
    """Strip OpenAI ``-YYYY-MM-DD`` snapshot suffix so Langfuse matches project model names."""
    if not api_model:
        return fallback
    m = _OPENAI_DATED_SNAPSHOT.match(api_model.strip())
    if m:
        return m.group(1)
    return api_model

