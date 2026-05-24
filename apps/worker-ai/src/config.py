import os
import sys

from dotenv import load_dotenv

load_dotenv("../../.env")
load_dotenv(".env")


def _warn_stderr(msg: str) -> None:
    print(msg, file=sys.stderr)


def _env_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def _parse_int(raw: str | None, env_name: str, default: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip(), 10)
        return value
    except ValueError:
        _warn_stderr(f"Warning: invalid {env_name}={raw!r}; using default {default}.")
        return default


def _parse_float(raw: str | None, env_name: str, default: float) -> float:
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw.strip())
        if value <= 0:
            raise ValueError("must be positive")
        return value
    except ValueError:
        _warn_stderr(f"Warning: invalid {env_name}={raw!r}; using default {default}.")
        return default


def _parse_bool(raw: str | None, env_name: str, default: bool) -> bool:
    if raw is None or raw.strip() == "":
        return default
    normalized = raw.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    _warn_stderr(f"Warning: invalid {env_name}={raw!r}; using default {default}.")
    return default


DATABASE_URL = _env_str("DATABASE_URL")
WORKER_USE_MOCK_RESULT = _parse_bool(
    os.getenv("WORKER_USE_MOCK_RESULT"), "WORKER_USE_MOCK_RESULT", False
)
WORKER_POLL_INTERVAL_SECONDS = _parse_int(
    os.getenv("WORKER_POLL_INTERVAL_SECONDS"), "WORKER_POLL_INTERVAL_SECONDS", 5
)
UPLOADS_DIR = _env_str("UPLOADS_DIR")

OPENAI_API_KEY = _env_str("OPENAI_API_KEY")
OPENAI_TIMEOUT = _parse_float(os.getenv("OPENAI_TIMEOUT"), "OPENAI_TIMEOUT", 120.0)
OPENAI_MAX_RETRIES = _parse_int(os.getenv("OPENAI_MAX_RETRIES"), "OPENAI_MAX_RETRIES", 2)
VISION_MAX_IMAGE_BYTES = _parse_int(
    os.getenv("VISION_MAX_IMAGE_BYTES"), "VISION_MAX_IMAGE_BYTES", 20971520
)
VISION_MAX_DIMENSION = _parse_int(
    os.getenv("VISION_MAX_DIMENSION"), "VISION_MAX_DIMENSION", 8192
)
OPENAI_VISION_MODEL = _env_str("OPENAI_VISION_MODEL", "gpt-4o")
OPENAI_TEXT_MODEL = _env_str("OPENAI_TEXT_MODEL", "gpt-4o")

LANGFUSE_PUBLIC_KEY = _env_str("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = _env_str("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = _env_str("LANGFUSE_HOST", "https://cloud.langfuse.com")


def langfuse_enabled() -> bool:
    return bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)


def validate() -> None:
    """Worker startup validation — DATABASE_URL only."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is required")


def validate_openai_config() -> None:
    """Call before running the AI pipeline."""
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is required to run the AI pipeline. "
            "Set it in .env or the environment."
        )
