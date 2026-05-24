"""Langfuse usage helpers and non-critical observability wrappers."""

from __future__ import annotations

import logging
from typing import Any, Callable, Protocol, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class GenerationLike(Protocol):
    def end(self, **kwargs: Any) -> None: ...


class SpanLike(Protocol):
    def end(self, **kwargs: Any) -> None: ...


class TraceLike(Protocol):
    def generation(self, **kwargs: Any) -> GenerationLike: ...

    def span(self, **kwargs: Any) -> SpanLike: ...

    def update(self, **kwargs: Any) -> None: ...


class NoOpGeneration:
    def end(self, **kwargs: Any) -> None:
        return None


class NoOpSpan:
    def end(self, **kwargs: Any) -> None:
        return None


class NoOpTrace:
    def generation(self, **kwargs: Any) -> NoOpGeneration:
        return NoOpGeneration()

    def span(self, **kwargs: Any) -> NoOpSpan:
        return NoOpSpan()

    def update(self, **kwargs: Any) -> None:
        return None


def token_count(usage: dict, *keys: str) -> int:
    """Return token count compatible with OpenAI and LangChain usage dicts."""
    for key in keys:
        value = usage.get(key)
        if isinstance(value, int):
            return value
    return 0


def summarize_usage(*usage_records: dict) -> dict:
    """Aggregate token usage across all pipeline model calls."""
    prompt_tokens = sum(
        token_count(usage, "prompt_tokens", "input_tokens") for usage in usage_records
    )
    completion_tokens = sum(
        token_count(usage, "completion_tokens", "output_tokens")
        for usage in usage_records
    )
    total_tokens = sum(
        token_count(usage, "total_tokens")
        or token_count(usage, "prompt_tokens", "input_tokens")
        + token_count(usage, "completion_tokens", "output_tokens")
        for usage in usage_records
    )
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def usage_details_for_langfuse(usage: dict) -> dict[str, int]:
    """Map token usage to Langfuse usage_details (input / output)."""
    details: dict[str, int] = {}
    inp = token_count(usage, "prompt_tokens", "input_tokens")
    out = token_count(usage, "completion_tokens", "output_tokens")
    if inp:
        details["input"] = inp
    if out:
        details["output"] = out
    return details


def safe_trace_start(
    enabled: bool,
    create_trace: Callable[[], tuple[Any, TraceLike]],
) -> tuple[Any, TraceLike]:
    """Start a Langfuse trace; fall back to no-op on failure."""
    if not enabled:
        return None, NoOpTrace()
    try:
        return create_trace()
    except Exception as exc:
        logger.warning("Langfuse trace start failed (non-critical): %s", exc)
        return None, NoOpTrace()


def safe_generation(trace: TraceLike, **kwargs: Any) -> GenerationLike:
    """Start a Langfuse generation span; fall back to no-op on failure."""
    try:
        return trace.generation(**kwargs)
    except Exception as exc:
        logger.warning("Langfuse generation start failed (non-critical): %s", exc)
        return NoOpGeneration()


def safe_generation_end(generation: GenerationLike, **kwargs: Any) -> None:
    """End a Langfuse generation span without failing the pipeline."""
    try:
        generation.end(**kwargs)
    except Exception as exc:
        logger.warning("Langfuse generation.end failed (non-critical): %s", exc)


def safe_span(trace: TraceLike, **kwargs: Any) -> SpanLike:
    """Start a Langfuse span; fall back to no-op on failure."""
    try:
        return trace.span(**kwargs)
    except Exception as exc:
        logger.warning("Langfuse span start failed (non-critical): %s", exc)
        return NoOpSpan()


def safe_span_end(span: SpanLike, **kwargs: Any) -> None:
    """End a Langfuse span without failing the pipeline."""
    try:
        span.end(**kwargs)
    except Exception as exc:
        logger.warning("Langfuse span.end failed (non-critical): %s", exc)


def safe_trace_update(trace: TraceLike, **kwargs: Any) -> None:
    """Update a Langfuse trace without failing the pipeline."""
    try:
        trace.update(**kwargs)
    except Exception as exc:
        logger.warning("Langfuse trace.update failed (non-critical): %s", exc)


def safe_flush(client: Any) -> None:
    """Flush Langfuse events without failing the pipeline."""
    if client is None:
        return
    try:
        client.flush()
    except Exception as exc:
        logger.warning("Langfuse flush failed (non-critical): %s", exc)
