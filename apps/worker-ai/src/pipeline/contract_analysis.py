"""Run the full contract comparison AI pipeline and return FinalAnalysisReport v1."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from agents.contextualization_agent import ContextualizationAgent, ContextualizationResult
from agents.extraction_agent import ExtractionAgent, ExtractionResult
from config import (
    LANGFUSE_HOST,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    OPENAI_API_KEY,
    OPENAI_TEXT_MODEL,
    langfuse_enabled,
    validate_openai_config,
)
from core.document_parser import parse_contract_document_with_metadata
from core.extraction_models import GranularContractChangeOutput
from core.granular_validation import normalize_granular_output, validate_granular_output
from core.image_parser import ImageParseResult
from core.models import StructuralContextMap
from infra.http_config import load_openai_runtime_config
from infra.langfuse_model import normalize_openai_model_for_langfuse
from pipeline.errors import (
    DocumentLoadError,
    PipelineError,
    mapping_error_from_validation,
    wrap_pipeline_exception,
)
from pipeline.observability import (
    TraceLike,
    safe_flush,
    safe_generation,
    safe_generation_end,
    safe_span,
    safe_span_end,
    safe_trace_start,
    safe_trace_update,
    summarize_usage,
    usage_details_for_langfuse,
)
from pipeline.result_mapper import map_extraction_to_final_report

logger = logging.getLogger(__name__)


def _validate_file_exists(path: str, label: str) -> Path:
    resolved = Path(path)
    if not resolved.is_file():
        raise DocumentLoadError(f"Document file not found ({label}): {path}")
    return resolved


def _build_openai_client() -> OpenAI:
    runtime = load_openai_runtime_config()
    return OpenAI(
        api_key=OPENAI_API_KEY,
        timeout=runtime.timeout,
        max_retries=runtime.max_retries,
    )


def _build_langfuse_client():
    from langfuse import Langfuse

    return Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST,
    )


def _create_langfuse_trace(
    analysis_job_id: str,
    original_path: str,
    amendment_path: str,
) -> tuple[Any, TraceLike]:
    client = _build_langfuse_client()
    trace = client.trace(
        name="contract-analysis",
        metadata={
            "original_image": original_path,
            "amendment_image": amendment_path,
            "analysis_job_id": analysis_job_id,
        },
        session_id=analysis_job_id,
    )
    return client, trace


def _run_vision_step(
    trace: TraceLike,
    *,
    step_label: str,
    generation_name: str,
    image_path: str,
    openai_client: OpenAI,
) -> ImageParseResult:
    logger.info("%s", step_label)
    generation = safe_generation(
        trace,
        name=generation_name,
        model=normalize_openai_model_for_langfuse(None),
        input={"image_path": image_path},
        metadata={"step": "vision_ocr"},
    )
    started = time.perf_counter()
    parse_result = parse_contract_document_with_metadata(image_path, client=openai_client)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    safe_generation_end(
        generation,
        output={
            "text_length": len(parse_result.text),
            "text_preview": parse_result.text[:300],
            "usage": parse_result.usage,
        },
        model=normalize_openai_model_for_langfuse(parse_result.model),
        usage_details=usage_details_for_langfuse(parse_result.usage),
        metadata={
            "latency_ms": elapsed_ms,
            "usage": parse_result.usage,
            **(
                {"openai_model": parse_result.model}
                if parse_result.model
                else {}
            ),
        },
    )
    logger.debug("%s done latency_ms=%d text_length=%d", step_label, elapsed_ms, len(parse_result.text))
    return parse_result


def _run_contextualization_step(
    trace: TraceLike,
    agent: ContextualizationAgent,
    *,
    analysis_job_id: str,
    original_text: str,
    amendment_text: str,
) -> ContextualizationResult:
    logger.info("job=%s step=3/4 contextualization", analysis_job_id)
    generation = safe_generation(
        trace,
        name="contextualization_agent",
        model=normalize_openai_model_for_langfuse(None),
        input={
            "original_text_length": len(original_text),
            "amendment_text_length": len(amendment_text),
        },
        metadata={"step": "context_mapping"},
    )
    started = time.perf_counter()
    result = agent.run_with_metadata(original_text, amendment_text)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    context_map_json = result.context_map.model_dump_json()
    ctx_model = normalize_openai_model_for_langfuse(result.model)
    safe_generation_end(
        generation,
        output={
            "context_map_json_length": len(context_map_json),
            "context_map_preview": context_map_json[:500],
            "usage": result.usage,
        },
        model=ctx_model,
        usage_details=usage_details_for_langfuse(result.usage),
        metadata={
            "latency_ms": elapsed_ms,
            "usage": result.usage,
            **({"openai_model": result.model} if result.model else {}),
        },
    )
    logger.debug(
        "job=%s step=3/4 done latency_ms=%d context_map_json_length=%d",
        analysis_job_id,
        elapsed_ms,
        len(context_map_json),
    )
    return result


def _run_extraction_step(
    trace: TraceLike,
    agent: ExtractionAgent,
    *,
    analysis_job_id: str,
    original_text: str,
    amendment_text: str,
    context_map: StructuralContextMap,
) -> ExtractionResult:
    logger.info("job=%s step=4/4 extraction", analysis_job_id)
    context_map_json = context_map.model_dump_json()
    generation = safe_generation(
        trace,
        name="extraction_agent",
        model=normalize_openai_model_for_langfuse(None),
        input={
            "original_text_length": len(original_text),
            "amendment_text_length": len(amendment_text),
            "context_map_json_length": len(context_map_json),
        },
        metadata={"step": "change_extraction"},
    )
    started = time.perf_counter()
    result = agent.run_with_metadata(original_text, amendment_text, context_map)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    ext_model = normalize_openai_model_for_langfuse(result.model)
    safe_generation_end(
        generation,
        output={
            "validated_output": result.output.model_dump(),
            "usage": result.usage,
        },
        model=ext_model,
        usage_details=usage_details_for_langfuse(result.usage),
        metadata={
            "latency_ms": elapsed_ms,
            "usage": result.usage,
            **({"openai_model": result.model} if result.model else {}),
        },
    )
    logger.debug("job=%s step=4/4 done latency_ms=%d", analysis_job_id, elapsed_ms)
    return result


def _run_semantic_validation_step(
    trace: TraceLike,
    output: GranularContractChangeOutput,
    *,
    analysis_job_id: str,
) -> GranularContractChangeOutput:
    logger.info("job=%s step=5/6 semantic validation", analysis_job_id)
    span = safe_span(
        trace,
        name="semantic_validation",
        input={"changes_count": len(output.changes)},
        metadata={"step": "semantic_validation"},
    )
    started = time.perf_counter()
    semantic_warnings = validate_granular_output(output)
    normalized = normalize_granular_output(output)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    safe_span_end(
        span,
        output={
            "warnings_count": len(normalized.extraction_warnings),
            "semantic_warnings": semantic_warnings[:20],
        },
        metadata={"latency_ms": elapsed_ms},
    )
    logger.debug(
        "job=%s step=5/6 done latency_ms=%d warnings_count=%d",
        analysis_job_id,
        elapsed_ms,
        len(normalized.extraction_warnings),
    )
    return normalized


def _run_result_mapping_step(
    trace: TraceLike,
    normalized_output: GranularContractChangeOutput,
    *,
    analysis_job_id: str,
) -> dict:
    logger.info("job=%s step=6/6 result mapping", analysis_job_id)
    span = safe_span(
        trace,
        name="result_mapping",
        input={"schema_version": normalized_output.schema_version},
        metadata={"step": "result_mapping"},
    )
    started = time.perf_counter()
    try:
        report = map_extraction_to_final_report(normalized_output)
    except ValidationError as exc:
        raise mapping_error_from_validation(exc) from exc
    except TypeError as exc:
        raise wrap_pipeline_exception(exc) from exc
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    validation = report.get("validation") or {}
    analysis_summary = report.get("analysis_summary") or {}
    safe_span_end(
        span,
        output={
            "validation_status": validation.get("status"),
            "total_changes": analysis_summary.get("total_changes"),
            "warnings_count": len(validation.get("warnings") or []),
        },
        metadata={"latency_ms": elapsed_ms},
    )
    logger.debug(
        "job=%s step=6/6 done latency_ms=%d validation_status=%s",
        analysis_job_id,
        elapsed_ms,
        validation.get("status"),
    )
    return report


def _finalize_trace(
    trace: TraceLike,
    langfuse_client: Any,
    *,
    report: dict,
    extraction_output: GranularContractChangeOutput,
    original_parse: ImageParseResult,
    amendment_parse: ImageParseResult,
    context_result: ContextualizationResult,
    extraction_result: ExtractionResult,
) -> None:
    total_usage = summarize_usage(
        original_parse.usage,
        amendment_parse.usage,
        context_result.usage,
        extraction_result.usage,
    )
    pipeline_models: list[str] = list(
        dict.fromkeys(
            [
                normalize_openai_model_for_langfuse(original_parse.model),
                normalize_openai_model_for_langfuse(amendment_parse.model),
                normalize_openai_model_for_langfuse(context_result.model),
                normalize_openai_model_for_langfuse(extraction_result.model),
            ]
        )
    )
    high_risk_count = sum(
        1
        for change in extraction_output.changes
        if change.risk_level in {"HIGH", "CRITICAL"}
    )
    validation = report.get("validation") or {}
    analysis_summary = report.get("analysis_summary") or {}
    trace_meta: dict = {
        "total_changes": len(extraction_output.changes),
        "high_risk_count": high_risk_count,
        "validation_status": validation.get("status"),
        "warnings_count": len(validation.get("warnings") or []),
        "overall_risk_level": analysis_summary.get("overall_risk_level"),
        "granular_schema_version": extraction_output.schema_version,
        "usage": total_usage,
        "models": pipeline_models,
    }
    if len(pipeline_models) == 1:
        trace_meta["model"] = pipeline_models[0]
    safe_trace_update(trace, output=report, metadata=trace_meta)
    safe_flush(langfuse_client)


def run_contract_analysis(
    analysis_job_id: str,
    original_file_path: str,
    amendment_file_path: str,
) -> dict:
    """
    Run the full contract-comparison pipeline.

    Steps:
      1. Parse original contract document (image -> Vision OCR, PDF -> local text)
      2. Parse amendment document (image -> Vision OCR, PDF -> local text)
      3. ContextualizationAgent → StructuralContextMap
      4. ExtractionAgent → GranularContractChangeOutput
      5. Semantic validation → normalized granular output
      6. Map to FinalAnalysisReport v1

    Returns a dict ready to persist as JSONB. Does not touch the database.
    When validation.status is INVALID the dict is still returned; the worker
    marks the job FAILED. VALID_WITH_WARNINGS completes successfully.

    Raises:
        PipelineError: when configuration, documents, OCR, agents, validation, or mapping fail.
        DocumentLoadError: when an input document path does not exist.
    """
    try:
        _validate_file_exists(original_file_path, "original")
        _validate_file_exists(amendment_file_path, "amendment")
        validate_openai_config()

        openai_client = _build_openai_client()
        contextualization_agent = ContextualizationAgent(model=OPENAI_TEXT_MODEL, temperature=0.0)
        extraction_agent = ExtractionAgent(model=OPENAI_TEXT_MODEL, temperature=0.0)

        langfuse_client, trace = safe_trace_start(
            langfuse_enabled(),
            lambda: _create_langfuse_trace(
                analysis_job_id,
                original_file_path,
                amendment_file_path,
            ),
        )

        original_parse = _run_vision_step(
            trace,
            step_label=f"job={analysis_job_id} step=1/4 parsing original contract",
            generation_name="parse_original_contract",
            image_path=original_file_path,
            openai_client=openai_client,
        )
        amendment_parse = _run_vision_step(
            trace,
            step_label=f"job={analysis_job_id} step=2/4 parsing amendment",
            generation_name="parse_amendment_contract",
            image_path=amendment_file_path,
            openai_client=openai_client,
        )

        context_result = _run_contextualization_step(
            trace,
            contextualization_agent,
            analysis_job_id=analysis_job_id,
            original_text=original_parse.text,
            amendment_text=amendment_parse.text,
        )
        extraction_result = _run_extraction_step(
            trace,
            extraction_agent,
            analysis_job_id=analysis_job_id,
            original_text=original_parse.text,
            amendment_text=amendment_parse.text,
            context_map=context_result.context_map,
        )

        extraction_output: GranularContractChangeOutput = extraction_result.output
        normalized_output = _run_semantic_validation_step(
            trace,
            extraction_output,
            analysis_job_id=analysis_job_id,
        )
        report = _run_result_mapping_step(
            trace,
            normalized_output,
            analysis_job_id=analysis_job_id,
        )

        validation = report.get("validation") or {}
        status = validation.get("status", "UNKNOWN")
        warnings_count = len(validation.get("warnings") or [])
        summary = report.get("analysis_summary") or {}

        _finalize_trace(
            trace,
            langfuse_client,
            report=report,
            extraction_output=normalized_output,
            original_parse=original_parse,
            amendment_parse=amendment_parse,
            context_result=context_result,
            extraction_result=extraction_result,
        )

        logger.info(
            "job=%s pipeline completed changes=%d validation_status=%s "
            "warnings_count=%d overall_risk_level=%s",
            analysis_job_id,
            len(report.get("changes") or []),
            status,
            warnings_count,
            summary.get("overall_risk_level"),
        )
        if status == "INVALID":
            logger.warning(
                "job=%s report validation_status=INVALID; worker will mark job FAILED",
                analysis_job_id,
            )
        return report

    except PipelineError:
        raise
    except Exception as exc:
        raise wrap_pipeline_exception(exc) from exc


if __name__ == "__main__":
    from pipeline.cli import main

    raise SystemExit(main())
