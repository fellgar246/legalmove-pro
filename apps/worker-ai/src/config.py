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
QUEUE_PROVIDER = _env_str("QUEUE_PROVIDER", "postgres")
WORKER_USE_MOCK_RESULT = _parse_bool(
    os.getenv("WORKER_USE_MOCK_RESULT"), "WORKER_USE_MOCK_RESULT", False
)
WORKER_POLL_INTERVAL_SECONDS = _parse_int(
    os.getenv("WORKER_POLL_INTERVAL_SECONDS"), "WORKER_POLL_INTERVAL_SECONDS", 5
)
UPLOADS_DIR = _env_str("UPLOADS_DIR")

AWS_REGION = _env_str("AWS_REGION")
S3_BUCKET = _env_str("S3_BUCKET")
S3_PREFIX = _env_str("S3_PREFIX")
DOCUMENT_TEMP_DIR = _env_str("DOCUMENT_TEMP_DIR", "./tmp/documents")

SQS_QUEUE_URL = _env_str("SQS_QUEUE_URL")
SQS_WAIT_TIME_SECONDS = _parse_int(
    os.getenv("SQS_WAIT_TIME_SECONDS"), "SQS_WAIT_TIME_SECONDS", 10
)
SQS_MAX_MESSAGES = _parse_int(os.getenv("SQS_MAX_MESSAGES"), "SQS_MAX_MESSAGES", 1)
_sqs_visibility_raw = os.getenv("SQS_VISIBILITY_TIMEOUT")
SQS_VISIBILITY_TIMEOUT = (
    _parse_int(_sqs_visibility_raw, "SQS_VISIBILITY_TIMEOUT", 60)
    if _sqs_visibility_raw is not None and _sqs_visibility_raw.strip() != ""
    else 60
)

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
    """Worker startup validation."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is required")
    validate_queue_config()


def validate_queue_config() -> None:
    """Validate queue provider configuration."""
    provider = (QUEUE_PROVIDER or "postgres").strip().lower()
    if provider == "sqs" and not SQS_QUEUE_URL:
        raise ValueError("SQS_QUEUE_URL is required when QUEUE_PROVIDER=sqs")


def validate_openai_config() -> None:
    """Call before running the AI pipeline."""
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is required to run the AI pipeline. "
            "Set it in .env or the environment."
        )
