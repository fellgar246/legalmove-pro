"""
Local PDF text extraction for contract documents.

Extracts embedded (selectable) text from text-based PDFs using ``pypdf`` —
fully local, no cloud services and no system dependencies. The result mirrors
``ImageParseResult`` so the rest of the pipeline is unchanged.

Scanned / image-only PDFs (no useful embedded text) are detected and rejected
with a clear message. Per-page OCR for those is intentionally left as a
documented seam (``_ocr_pdf_fallback``) and not implemented in this milestone.
"""

from __future__ import annotations

import logging
from pathlib import Path

from openai import OpenAI
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from core.image_parser import ImageParseResult
from infra.http_config import load_pdf_limits

logger = logging.getLogger(__name__)

_PDF_EXTENSION = ".pdf"

# Model/source tag recorded for observability when text comes from local
# extraction rather than an OpenAI model. Safe for Langfuse (treated as metadata).
LOCAL_PDF_TEXT_SOURCE = "local-pdf-text"


def _validate_pdf_path(pdf_path: str) -> Path:
    """Ensure the path exists and has a ``.pdf`` extension."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if path.suffix.lower() != _PDF_EXTENSION:
        raise ValueError(
            f"Not a valid PDF: expected a '.pdf' file, got '{path.suffix}'."
        )
    return path


def _enforce_pdf_size(path: Path, max_bytes: int) -> None:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise OSError(f"Cannot read PDF file metadata: {path}") from exc
    if size == 0:
        raise ValueError(f"PDF file is empty: {path}")
    if size > max_bytes:
        raise ValueError(
            f"PDF file is too large ({size} bytes). "
            f"Maximum allowed is {max_bytes} bytes (set PDF_MAX_BYTES)."
        )


def _open_pdf(path: Path) -> PdfReader:
    """Open a PDF, handling corrupt files and (empty-password) encryption."""
    try:
        reader = PdfReader(str(path))
    except (PdfReadError, ValueError, OSError) as exc:
        raise ValueError(
            f"Not a valid PDF (corrupt or unreadable): {path}"
        ) from exc

    if reader.is_encrypted:
        # Many "encrypted" PDFs only carry an empty owner password; try that.
        try:
            decrypt_result = reader.decrypt("")
        except Exception as exc:  # pypdf raises various errors for unsupported crypto
            raise ValueError(
                f"PDF is encrypted and cannot be opened without a password: {path}"
            ) from exc
        if not decrypt_result:
            raise ValueError(
                f"PDF is encrypted and cannot be opened without a password: {path}"
            )
    return reader


def _extract_embedded_text(reader: PdfReader) -> str:
    """Concatenate embedded text from every page, skipping unreadable pages."""
    parts: list[str] = []
    for index, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
        except Exception as exc:  # one bad page must not abort the whole document
            logger.warning("pdf page %d text extraction failed: %s", index, exc)
            page_text = ""
        if page_text.strip():
            parts.append(page_text.strip())
    return "\n\n".join(parts)


def _visible_char_count(text: str) -> int:
    """Count non-whitespace characters (whitespace-only PDFs are 'empty')."""
    return sum(1 for ch in text if not ch.isspace())


def _scanned_pdf_message(path: Path) -> str:
    return (
        "PDF appears to be scanned or image-only: no extractable embedded text "
        f"was found in {path.name}. Per-page OCR fallback for scanned PDFs is not "
        "enabled in local mode yet (Milestone 2.3, Bloque 1). Provide a "
        "text-based PDF, or upload the document pages as images to use Vision OCR."
    )


def _ocr_pdf_fallback(path: Path, client: OpenAI | None = None) -> ImageParseResult:
    """
    Seam for future per-page OCR of scanned PDFs.

    Intentionally not implemented in this milestone (Bloque 1). The intended
    approach is: rasterize each page to an image, run the existing Vision OCR
    per page, then concatenate. Implementing it now would pull in rendering
    dependencies (e.g. a PDF-to-image backend) that are out of scope here.
    """
    raise NotImplementedError(
        "Per-page OCR fallback for scanned PDFs is not implemented yet."
    )


def parse_contract_pdf_with_metadata(
    pdf_path: str,
    client: OpenAI | None = None,
) -> ImageParseResult:
    """
    Extract contract text from a text-based PDF locally.

    Args:
        pdf_path: Path to a ``.pdf`` file.
        client: Accepted for signature symmetry with the image parser and the
            future OCR fallback; unused for embedded-text extraction.

    Returns:
        ImageParseResult with extracted text, ``model=LOCAL_PDF_TEXT_SOURCE``,
        and an empty usage dict (no token cost for local extraction).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: Wrong extension, empty/oversized file, corrupt or encrypted
            PDF, or a scanned/image-only PDF with no extractable text.
        OSError: File metadata/read failures.
    """
    path = _validate_pdf_path(pdf_path)
    limits = load_pdf_limits()
    _enforce_pdf_size(path, limits.max_bytes)

    reader = _open_pdf(path)
    text = _extract_embedded_text(reader).strip()

    if _visible_char_count(text) < limits.min_text_chars:
        # Scanned/empty: route would be _ocr_pdf_fallback() once implemented.
        raise ValueError(_scanned_pdf_message(path))

    logger.debug(
        "pdf parsed locally path=%s pages=%d text_length=%d",
        path.name,
        len(reader.pages),
        len(text),
    )
    return ImageParseResult(text=text, model=LOCAL_PDF_TEXT_SOURCE, usage={})


def parse_contract_pdf(pdf_path: str, client: OpenAI | None = None) -> str:
    """Convenience wrapper returning only the extracted text."""
    return parse_contract_pdf_with_metadata(pdf_path, client=client).text
