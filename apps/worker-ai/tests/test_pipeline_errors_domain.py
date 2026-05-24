import sys
from pathlib import Path
from unittest.mock import MagicMock

import openai
import pytest
from pydantic import BaseModel, ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pipeline.errors import (
    AgentExecutionError,
    DocumentLoadError,
    OCRExtractionError,
    OutputValidationError,
    PipelineError,
    ResultMappingError,
    wrap_pipeline_exception,
)


class _SampleModel(BaseModel):
    name: str


def test_wrap_file_not_found_as_document_load_error():
    wrapped = wrap_pipeline_exception(FileNotFoundError("Image not found: /tmp/a.png"))
    assert isinstance(wrapped, DocumentLoadError)
    assert "Image not found" in str(wrapped)


def test_wrap_unsupported_image_as_document_load_error():
    wrapped = wrap_pipeline_exception(
        ValueError("Unsupported image format '.pdf'. Supported: ['.png']")
    )
    assert isinstance(wrapped, DocumentLoadError)


def test_wrap_ocr_truncated_response_as_ocr_error():
    wrapped = wrap_pipeline_exception(
        ValueError(
            "Vision OCR response was truncated (finish_reason=length). "
            "The completion hit max_tokens=4096."
        )
    )
    assert isinstance(wrapped, OCRExtractionError)
    assert "truncated" in str(wrapped).lower()


def test_wrap_rate_limit_as_agent_execution_error():
    response = MagicMock()
    response.headers = {}
    response.json.return_value = {}
    response.text = ""
    exc = openai.RateLimitError(
        "rate limit",
        response=response,
        body=None,
    )
    wrapped = wrap_pipeline_exception(exc)
    assert isinstance(wrapped, AgentExecutionError)
    assert "rate limit" in str(wrapped).lower()


def test_wrap_timeout_as_agent_execution_error():
    exc = openai.APITimeoutError(request=MagicMock())
    wrapped = wrap_pipeline_exception(exc)
    assert isinstance(wrapped, AgentExecutionError)
    assert "timed out" in str(wrapped).lower()


def test_wrap_pydantic_validation_as_output_validation_error():
    try:
        _SampleModel.model_validate({})
    except ValidationError as exc:
        wrapped = wrap_pipeline_exception(exc)
    else:
        pytest.fail("expected ValidationError")

    assert isinstance(wrapped, OutputValidationError)
    assert "AI output validation failed" in str(wrapped)


def test_wrap_structured_output_value_error():
    wrapped = wrap_pipeline_exception(
        ValueError("[ExtractionAgent] Output does not match the Pydantic schema:\n  • name: required")
    )
    assert isinstance(wrapped, OutputValidationError)
    assert "AI output validation failed" in str(wrapped)


def test_wrap_mapper_type_error_as_result_mapping_error():
    wrapped = wrap_pipeline_exception(
        TypeError("raw_output must be a ContractChangeOutput instance or a compatible dict")
    )
    assert isinstance(wrapped, ResultMappingError)
    assert "Failed to build analysis report" in str(wrapped)


def test_wrap_missing_api_key_as_pipeline_error():
    wrapped = wrap_pipeline_exception(
        ValueError("OPENAI_API_KEY is required to run the AI pipeline.")
    )
    assert isinstance(wrapped, PipelineError)
    assert "OPENAI_API_KEY" in str(wrapped)


def test_wrap_unknown_error_as_generic_pipeline_error():
    wrapped = wrap_pipeline_exception(RuntimeError("something broke internally"))
    assert isinstance(wrapped, PipelineError)
    assert str(wrapped) == "An unexpected error occurred during contract analysis."


def test_wrap_pipeline_error_is_idempotent():
    original = DocumentLoadError("already wrapped")
    assert wrap_pipeline_exception(original) is original
