"""
Document parsing dispatcher: route a contract file to the right extractor.

This is the single entry point the pipeline uses to turn an uploaded file into
contract text. It keeps the existing image OCR flow untouched and adds native
PDF support:

  - Images (.jpg/.jpeg/.png/.webp/.gif) -> GPT-4o Vision OCR (unchanged).
  - PDFs (text-based)                    -> local embedded-text extraction.
  - Scanned PDFs / unknown types         -> clear, user-facing errors.

All paths return the same ``ImageParseResult`` contract, so nothing downstream
(contextualization, extraction, validation, FinalAnalysisReport v1) changes.
"""

from __future__ import annotations

import logging
from pathlib import Path

from openai import OpenAI

from core.image_parser import (
    SUPPORTED_IMAGE_EXTENSIONS,
    ImageParseResult,
    parse_contract_image_with_metadata,
)
from core.pdf_parser import parse_contract_pdf_with_metadata

logger = logging.getLogger(__name__)

_PDF_MAGIC = b"%PDF-"
# Per the PDF spec the header may appear within the first 1024 bytes.
_PDF_MAGIC_SCAN_WINDOW = 1024
_PDF_EXTENSION = ".pdf"

DOCUMENT_TYPE_PDF = "pdf"
DOCUMENT_TYPE_IMAGE = "image"


def _has_pdf_magic(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            header = fh.read(_PDF_MAGIC_SCAN_WINDOW)
    except OSError:
        return False
    return _PDF_MAGIC in header


def detect_document_type(path: Path) -> str:
    """
    Classify a document as ``"pdf"`` or ``"image"``.

    Content sniffing (PDF magic bytes) takes precedence over the extension so a
    mislabeled file is still handled correctly. Falls back to the extension and
    raises ``ValueError`` for anything we do not support.
    """
    if _has_pdf_magic(path):
        return DOCUMENT_TYPE_PDF

    suffix = path.suffix.lower()
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return DOCUMENT_TYPE_IMAGE
    if suffix == _PDF_EXTENSION:
        # Extension says PDF but magic bytes were missing; let the PDF parser
        # produce a precise "not a valid PDF" error.
        return DOCUMENT_TYPE_PDF

    supported = sorted(SUPPORTED_IMAGE_EXTENSIONS) + [_PDF_EXTENSION]
    raise ValueError(
        f"Unsupported document format '{suffix or path.name}'. "
        f"Supported formats: {supported}."
    )


def parse_contract_document_with_metadata(
    file_path: str,
    client: OpenAI | None = None,
) -> ImageParseResult:
    """
    Extract contract text from an image or PDF and return extraction metadata.

    Args:
        file_path: Path to a supported document (image or PDF).
        client: Shared OpenAI client used by the image OCR path. PDFs with
            embedded text do not call OpenAI.

    Returns:
        ImageParseResult (text, model, usage) regardless of source type.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: Unsupported format, or downstream parser validation errors.
        OSError: File read/decoding failures.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    document_type = detect_document_type(path)
    logger.debug("document type detected path=%s type=%s", path.name, document_type)

    if document_type == DOCUMENT_TYPE_PDF:
        return parse_contract_pdf_with_metadata(str(path), client=client)
    return parse_contract_image_with_metadata(str(path), client=client)


def parse_contract_document(file_path: str, client: OpenAI | None = None) -> str:
    """Convenience wrapper returning only the extracted text."""
    return parse_contract_document_with_metadata(file_path, client=client).text
