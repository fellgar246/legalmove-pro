"""
User-facing error messages for OpenAI HTTP/SDK failures (without leaking secrets).

Also detects context-window errors that surface as BadRequestError or buried in causes.
"""

from __future__ import annotations

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None


def _iter_exception_chain(exc: BaseException):
    visited: set[int] = set()
    cur: BaseException | None = exc
    while cur is not None and id(cur) not in visited:
        visited.add(id(cur))
        yield cur
        cur = cur.__cause__ or cur.__context__


def _collect_error_text(exc: BaseException) -> str:
    parts: list[str] = []
    for e in _iter_exception_chain(exc):
        parts.append(str(e))
        resp = getattr(e, "response", None)
        if resp is not None:
            try:
                json_data = getattr(resp, "json", lambda: {})()
                if isinstance(json_data, dict):
                    err = json_data.get("error")
                    if isinstance(err, dict) and err.get("message"):
                        parts.append(str(err["message"]))
                    elif isinstance(err, dict) and err.get("code"):
                        parts.append(str(err.get("code")))
            except Exception:
                pass
            try:
                text = getattr(resp, "text", "") or ""
                if text:
                    parts.append(text[:2000])
            except Exception:
                pass
    return " ".join(parts).lower()


def describes_context_length_exceeded(exc: BaseException) -> bool:
    """True if the exception chain indicates the model context limit was exceeded."""
    blob = _collect_error_text(exc)
    return any(
        token in blob
        for token in (
            "context_length_exceeded",
            "maximum context length",
            "token limit",
            "too many tokens",
            "context window",
            "requested too many tokens",
        )
    )


def format_openai_related_error(exc: BaseException) -> str | None:
    """
    Return a concise stderr-safe message for known API/network failures, or None if unknown.
    """
    if openai is None:
        return None

    if describes_context_length_exceeded(exc):
        return (
            "The input is too large for the model context window. "
            "Try shorter documents, summarization, or splitting the contract into parts."
        )

    for e in _iter_exception_chain(exc):
        if isinstance(e, openai.RateLimitError):
            extra = ""
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    ra = resp.headers.get("retry-after") or resp.headers.get("Retry-After")
                    if ra:
                        extra = f" Retry after: {ra}s."
                except Exception:
                    pass
            return (
                "OpenAI rate limit reached (HTTP 429). Wait and try again, or reduce request frequency."
                + extra
            )

        if isinstance(e, openai.APITimeoutError):
            return (
                "OpenAI request timed out. Check your network, increase OPENAI_TIMEOUT, or retry later."
            )

        if isinstance(e, openai.APIConnectionError):
            return (
                "Could not reach the OpenAI API (connection error). Check your network and DNS."
            )

        if isinstance(e, openai.AuthenticationError):
            return "OpenAI authentication failed. Verify OPENAI_API_KEY in your environment."

        if isinstance(e, openai.PermissionDeniedError):
            return "OpenAI permission denied for this resource or model."

        if isinstance(e, openai.BadRequestError):
            return (
                "OpenAI rejected the request (400 Bad Request). "
                "The prompt or parameters may be invalid for the selected model."
            )

        if isinstance(e, openai.APIError):
            body = getattr(e, "body", None)
            msg = str(e)
            if body is not None and str(body).strip():
                msg = f"{msg} ({body})"
            return f"OpenAI API error: {msg}"

    return None


def is_openai_related_exception(exc: BaseException) -> bool:
    """True if exception is in OpenAI SDK hierarchy anywhere in the chain."""
    if openai is None:
        return False
    return any(isinstance(e, openai.APIError) for e in _iter_exception_chain(exc))


def maybe_wrap_context_limit_error(exc: BaseException) -> ValueError | None:
    """
    If the exception indicates the model hit its context-window limit,
    return a ValueError carrying a clearer message for the CLI layer.

    LangChain/agent invoke paths often propagate OpenAI exceptions without
    re-labeling them; wrapping here keeps UX consistent across agents.
    """
    if openai is None:
        return None
    if not describes_context_length_exceeded(exc):
        return None
    msg = format_openai_related_error(exc) or (
        "The input is too large for the model context window. "
        "Try shorter documents, summarization, or splitting the contract into parts."
    )
    return ValueError(msg)
