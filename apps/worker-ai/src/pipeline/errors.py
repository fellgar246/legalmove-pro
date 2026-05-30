"""Domain exceptions for the contract analysis pipeline."""

from __future__ import annotations

from pydantic import ValidationError

from core.validation_utils import format_pydantic_validation_error
from infra.openai_errors import format_openai_related_error, is_openai_related_exception

_MAX_USER_MESSAGE_LEN = 500

_DOCUMENT_VALUE_MARKERS = (
    "unsupported image format",
    "image file is empty",
    "image file is too large",
    "image dimensions",
    "not a valid decodable image",
    "cannot read image file",
    "cannot read or decode image",
    "image not found",
    "image format",
    "unsupported document format",
    "document not found",
    "pdf not found",
    "not a valid pdf",
    "pdf file is empty",
    "pdf file is too large",
    "cannot read pdf",
    "pdf is encrypted",
    "pdf appears to be scanned",
    "no extractable embedded text",
)

_OCR_VALUE_MARKERS = (
    "openai vision returned no choices",
    "vision ocr response was truncated",
    "finish_reason=length",
)

_STRUCTURED_OUTPUT_MARKERS = (
    "output does not match the pydantic schema",
    "structured output parsing failed",
)


class PipelineError(Exception):
    """Base domain error; str(self) is safe for analysis_jobs.error_message."""


class DocumentLoadError(PipelineError):
    """Document file missing, unreadable, or invalid for processing."""


class OCRExtractionError(PipelineError):
    """Vision OCR failed or returned an incomplete response."""


class AgentExecutionError(PipelineError):
    """OpenAI agent or API call failed during analysis."""


class OutputValidationError(PipelineError):
    """AI structured output failed schema validation."""


class ResultMappingError(PipelineError):
    """FinalAnalysisReport mapping failed."""


def _truncate_message(message: str) -> str:
    if len(message) <= _MAX_USER_MESSAGE_LEN:
        return message
    return message[: _MAX_USER_MESSAGE_LEN - 3] + "..."


def _normalize_message(message: str) -> str:
    return _truncate_message(message.strip())


def _is_document_validation_error(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in _DOCUMENT_VALUE_MARKERS)


def _is_ocr_validation_error(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in _OCR_VALUE_MARKERS)


def _is_structured_output_error(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in _STRUCTURED_OUTPUT_MARKERS)


def _format_validation_error_message(err: ValidationError) -> str:
    body = format_pydantic_validation_error(err).replace("\n", "; ")
    return _normalize_message(f"AI output validation failed: {body}")


def mapping_error_from_validation(err: ValidationError) -> ResultMappingError:
    body = format_pydantic_validation_error(err).replace("\n", "; ")
    return ResultMappingError(_normalize_message(f"Failed to build analysis report: {body}"))


def wrap_pipeline_exception(exc: BaseException) -> PipelineError:
    """Map a technical exception to a user-facing pipeline domain error."""
    if isinstance(exc, PipelineError):
        return exc

    if isinstance(exc, FileNotFoundError):
        return DocumentLoadError(_normalize_message(str(exc)))

    if isinstance(exc, ValidationError):
        return OutputValidationError(_format_validation_error_message(exc))

    if isinstance(exc, TypeError):
        message = str(exc)
        if "raw_output must be" in message:
            return ResultMappingError(
                _normalize_message(
                    "Failed to build analysis report: invalid extraction output type."
                )
            )
        return PipelineError(
            _normalize_message(
                "An unexpected error occurred during contract analysis.")
        )

    if isinstance(exc, ValueError):
        message = str(exc)
        if "OPENAI_API_KEY" in message:
            return PipelineError(_normalize_message(message))
        if _is_structured_output_error(message):
            summary = message.split("\n", 1)[0]
            return OutputValidationError(
                _normalize_message(f"AI output validation failed: {summary}")
            )
        if _is_ocr_validation_error(message):
            return OCRExtractionError(_normalize_message(message))
        if _is_document_validation_error(message) or "document file not found" in message.lower():
            return DocumentLoadError(_normalize_message(message))
        formatted_openai = format_openai_related_error(exc)
        if formatted_openai is not None:
            return AgentExecutionError(_normalize_message(formatted_openai))
        return PipelineError(
            _normalize_message(
                "An unexpected error occurred during contract analysis.")
        )

    if isinstance(exc, OSError):
        message = str(exc)
        if any(
            token in message.lower()
            for token in ("image", "decode", "read", "metadata")
        ):
            return DocumentLoadError(_normalize_message(message))
        return PipelineError(
            _normalize_message(
                "An unexpected error occurred during contract analysis.")
        )

    formatted_openai = format_openai_related_error(exc)
    if formatted_openai is not None:
        return AgentExecutionError(_normalize_message(formatted_openai))

    if is_openai_related_exception(exc):
        return AgentExecutionError(
            _normalize_message(
                "OpenAI API error. Check worker logs for details.")
        )

    return PipelineError(
        _normalize_message(
            "An unexpected error occurred during contract analysis.")
    )
