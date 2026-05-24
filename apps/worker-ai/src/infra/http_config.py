"""
Centralized HTTP/OpenAI timing and Vision image limits from environment.

Defaults apply when variables are unset; invalid values log a stderr warning and fall back.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from functools import lru_cache

DEFAULT_OPENAI_TIMEOUT = 120.0
DEFAULT_OPENAI_MAX_RETRIES = 2
DEFAULT_VISION_MAX_IMAGE_BYTES = 20 * 1024 * 1024
DEFAULT_VISION_MAX_DIMENSION = 8192


def _warn_stderr(msg: str) -> None:
    print(msg, file=sys.stderr)


def _parse_positive_float(raw: str | None, env_name: str, default: float) -> float:
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw.strip())
        if value <= 0:
            raise ValueError("must be positive")
        return value
    except ValueError:
        _warn_stderr(
            f"Warning: invalid {env_name}={raw!r}; "
            f"using default {default} seconds."
        )
        return default


def _parse_non_negative_int(raw: str | None, env_name: str, default: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip(), 10)
        if value < 0:
            raise ValueError("must be non-negative")
        return value
    except ValueError:
        _warn_stderr(
            f"Warning: invalid {env_name}={raw!r}; using default {default}."
        )
        return default


def _parse_positive_int(raw: str | None, env_name: str, default: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip(), 10)
        if value <= 0:
            raise ValueError("must be positive")
        return value
    except ValueError:
        _warn_stderr(
            f"Warning: invalid {env_name}={raw!r}; using default {default}."
        )
        return default


@dataclass(frozen=True)
class OpenAIRuntimeConfig:
    """Timeout (seconds per request) and SDK-level retries for OpenAI HTTP calls."""

    timeout: float
    max_retries: int


@dataclass(frozen=True)
class VisionLimits:
    max_image_bytes: int
    max_dimension: int


@lru_cache(maxsize=1)
def load_openai_runtime_config() -> OpenAIRuntimeConfig:
    return OpenAIRuntimeConfig(
        timeout=_parse_positive_float(os.getenv("OPENAI_TIMEOUT"), "OPENAI_TIMEOUT", DEFAULT_OPENAI_TIMEOUT),
        max_retries=_parse_non_negative_int(
            os.getenv("OPENAI_MAX_RETRIES"), "OPENAI_MAX_RETRIES", DEFAULT_OPENAI_MAX_RETRIES
        ),
    )


@lru_cache(maxsize=1)
def load_vision_limits() -> VisionLimits:
    return VisionLimits(
        max_image_bytes=_parse_positive_int(
            os.getenv("VISION_MAX_IMAGE_BYTES"),
            "VISION_MAX_IMAGE_BYTES",
            DEFAULT_VISION_MAX_IMAGE_BYTES,
        ),
        max_dimension=_parse_positive_int(
            os.getenv("VISION_MAX_DIMENSION"),
            "VISION_MAX_DIMENSION",
            DEFAULT_VISION_MAX_DIMENSION,
        ),
    )
