"""
Multimodal helpers to parse contract scan images.

Provides validation, base64 encoding, and GPT-4o Vision calls to extract full
document text from image files.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError
from openai import OpenAI

from config import OPENAI_VISION_MODEL
from infra.http_config import load_openai_runtime_config, load_vision_limits

_SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

_PIL_FORMAT_TO_MIME = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "GIF": "image/gif",
}

_MAX_VISION_COMPLETION_TOKENS = 4096

_VISION_SYSTEM_PROMPT = (
    "You are a legal document OCR specialist. "
    "Your task is to extract ALL the text from the contract image provided, "
    "preserving the original structure as faithfully as possible: "
    "section headings, clause numbers, paragraph breaks, and formatting cues. "
    "Do not summarize, paraphrase, or omit any content. "
    "If a portion of the image is unreadable, mark it as [ILLEGIBLE]. "
    "Output only the extracted text — no commentary, no markdown fences."
)


@dataclass(frozen=True)
class ImageParseResult:
    """Multimodal OCR result plus model name and API token usage."""

    text: str
    model: str
    usage: dict[str, Any]


def _validate_image_path(image_path: str) -> Path:
    """Ensure the path exists and has a supported extension."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format '{path.suffix}'. "
            f"Supported: {sorted(_SUPPORTED_EXTENSIONS)}"
        )
    return path


def _enforce_file_size(path: Path, max_bytes: int) -> None:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise OSError(f"Cannot read image file metadata: {path}") from exc
    if size == 0:
        raise ValueError(f"Image file is empty: {path}")
    if size > max_bytes:
        raise ValueError(
            f"Image file is too large ({size} bytes). "
            f"Maximum allowed is {max_bytes} bytes (set VISION_MAX_IMAGE_BYTES)."
        )


def _inspect_image_with_pillow(path: Path, max_dimension: int) -> tuple[str, int, int]:
    """
    Verify the image decodes and respects max dimension; returns (mime_type, width, height).

    MIME reflects the format Pillow detected (not just the file extension).
    """
    try:
        with Image.open(path) as img:
            img.load()
            fmt = img.format
            width, height = img.size
    except UnidentifiedImageError as exc:
        raise ValueError(
            f"File is not a valid decodable image (corrupt or wrong type): {path}"
        ) from exc
    except OSError as exc:
        raise OSError(f"Cannot read or decode image: {path}") from exc

    if not fmt or fmt not in _PIL_FORMAT_TO_MIME:
        raise ValueError(
            f"Image format {fmt!r} is not supported for contract parsing. "
            f"Use one of: {sorted(_PIL_FORMAT_TO_MIME.keys())}."
        )

    side = max(width, height)
    if side > max_dimension:
        raise ValueError(
            f"Image dimensions {width}x{height} exceed limit {max_dimension}px "
            f"on the long side (set VISION_MAX_DIMENSION)."
        )

    return _PIL_FORMAT_TO_MIME[fmt], width, height


def _read_file_as_base64(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise OSError(f"Cannot read image file: {path}") from exc
    return base64.b64encode(raw).decode("utf-8")


def _usage_to_dict(usage: Any) -> dict[str, Any]:
    """Normalize token-usage metadata from the OpenAI SDK into a plain dict."""
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    if isinstance(usage, dict):
        return usage
    return {}


def _openai_client_or_default(client: OpenAI | None) -> OpenAI:
    if client is not None:
        return client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Load a .env file or pass an OpenAI client instance."
        )
    cfg = load_openai_runtime_config()
    return OpenAI(api_key=api_key, timeout=cfg.timeout, max_retries=cfg.max_retries)


def parse_contract_image_with_metadata(
    image_path: str,
    client: OpenAI | None = None,
) -> ImageParseResult:
    """
    Run GPT-4o Vision OCR and return plaintext plus usage metadata.

    Encodes the image as base64 and sends it to OpenAI with a legal-document
    OCR-focused system prompt.

    Args:
        image_path: Absolute or relative path (JPEG, PNG, WEBP, GIF).
        client: Shared OpenAI client. If ``None``, a client is constructed from
            ``OPENAI_API_KEY``, ``OPENAI_TIMEOUT``, and ``OPENAI_MAX_RETRIES``.

    Returns:
        ImageParseResult with extracted text, model id, and token usage dict.

    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: Unsupported format, empty file, dimension limits exceeded,
            or Vision response truncated at ``max_tokens``.
        OSError: File read/decoding failures.
        EnvironmentError: If ``client`` is ``None`` and ``OPENAI_API_KEY`` is unset.
    """
    path = _validate_image_path(image_path)
    limits = load_vision_limits()
    _enforce_file_size(path, limits.max_image_bytes)
    mime_type, _w, _h = _inspect_image_with_pillow(path, limits.max_dimension)
    base64_data = _read_file_as_base64(path)

    client = _openai_client_or_default(client)

    response = client.chat.completions.create(
        model=OPENAI_VISION_MODEL,
        messages=[
            {
                "role": "system",
                "content": _VISION_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_data}",
                            "detail": "high",
                        },
                    },
                    {
                        "type": "text",
                        "text": "Extract all text from this contract document.",
                    },
                ],
            },
        ],
        max_tokens=_MAX_VISION_COMPLETION_TOKENS,
        temperature=0,
    )

    if not response.choices:
        raise ValueError("OpenAI Vision returned no choices.")

    choice0 = response.choices[0]
    finish_reason = getattr(choice0, "finish_reason", None)
    if finish_reason == "length":
        raise ValueError(
            "Vision OCR response was truncated (finish_reason=length). "
            f"The completion hit max_tokens={_MAX_VISION_COMPLETION_TOKENS}. "
            "Split the document into pages or raise max_tokens in code for long scans."
        )

    return ImageParseResult(
        text=choice0.message.content or "",
        model=response.model,
        usage=_usage_to_dict(response.usage),
    )


def parse_contract_image(image_path: str, client: OpenAI | None = None) -> str:
    """
    Extract full contract text from an image using GPT-4o Vision.

    Backwards-compatible convenience wrapper. For full model/token metadata,
    use ``parse_contract_image_with_metadata()``.
    """
    return parse_contract_image_with_metadata(image_path, client=client).text
