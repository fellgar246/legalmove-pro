import logging
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.extraction_models import GRANULAR_SCHEMA_VERSION, GranularContractChangeOutput
from core.image_parser import ImageParseResult
from pipeline import contract_analysis
from pipeline.contract_analysis import run_contract_analysis
from tests.fixtures import sample_granular_extraction_output, sample_granular_low_confidence


def _write_image_files(tmp_path: Path) -> tuple[Path, Path]:
    original = tmp_path / "orig.png"
    amendment = tmp_path / "amend.png"
    original.write_bytes(b"x")
    amendment.write_bytes(b"x")
    return original, amendment


@contextmanager
def _patch_pipeline_agents(monkeypatch, *, extraction_output):
    monkeypatch.setattr(contract_analysis, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(contract_analysis, "langfuse_enabled", lambda: False)

    context_map = MagicMock()
    context_map.model_dump_json.return_value = "{}"

    with patch.object(
        contract_analysis,
        "parse_contract_document_with_metadata",
        side_effect=[
            ImageParseResult(text="original text", model="gpt-4o", usage={}),
            ImageParseResult(text="amendment text", model="gpt-4o", usage={}),
        ],
    ):
        with patch.object(contract_analysis, "ContextualizationAgent") as ctx_cls:
            with patch.object(contract_analysis, "ExtractionAgent") as ext_cls:
                ctx_cls.return_value.run_with_metadata.return_value = MagicMock(
                    context_map=context_map,
                    model="gpt-4o",
                    usage={},
                )
                ext_cls.return_value.run_with_metadata.return_value = MagicMock(
                    output=extraction_output,
                    model="gpt-4o",
                    usage={},
                )
                yield


def test_pipeline_applies_semantic_validation_and_mapping(tmp_path, monkeypatch):
    original, amendment = _write_image_files(tmp_path)

    with _patch_pipeline_agents(
        monkeypatch, extraction_output=sample_granular_extraction_output()
    ):
        report = run_contract_analysis(
            analysis_job_id="test-granular-job",
            original_file_path=str(original),
            amendment_file_path=str(amendment),
        )

    assert report["schema_version"] == "1.0"
    assert report["analysis_summary"]["total_changes"] == 2
    assert report["validation"]["status"] == "VALID"
    assert len(report["changes"]) == 2
    assert report["changes"][0].get("evidence") is not None
    assert report["changes"][0].get("confidence") == "HIGH"


def test_pipeline_valid_with_warnings_completes(tmp_path, monkeypatch):
    original, amendment = _write_image_files(tmp_path)

    with _patch_pipeline_agents(
        monkeypatch, extraction_output=sample_granular_low_confidence()
    ):
        report = run_contract_analysis(
            analysis_job_id="test-warnings-job",
            original_file_path=str(original),
            amendment_file_path=str(amendment),
        )

    assert report["validation"]["status"] == "VALID_WITH_WARNINGS"
    assert report["changes"][0]["requires_human_review"] is True
    assert len(report["validation"]["warnings"]) > 0


def test_pipeline_returns_invalid_report_without_raising(tmp_path, monkeypatch):
    original, amendment = _write_image_files(tmp_path)

    invalid_output = GranularContractChangeOutput.model_construct(
        schema_version=GRANULAR_SCHEMA_VERSION,
        executive_summary="",
        overall_risk_level="MEDIUM",
        changes=[],
        key_risks=[],
        human_review_recommendations=[],
        extraction_warnings=[],
    )

    with _patch_pipeline_agents(monkeypatch, extraction_output=invalid_output):
        report = run_contract_analysis(
            analysis_job_id="test-invalid-job",
            original_file_path=str(original),
            amendment_file_path=str(amendment),
        )

    assert report["validation"]["status"] == "INVALID"
    assert report["changes"] == []


def test_semantic_validation_span_non_blocking(tmp_path, monkeypatch):
    original, amendment = _write_image_files(tmp_path)
    monkeypatch.setattr(contract_analysis, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(contract_analysis, "langfuse_enabled", lambda: True)

    context_map = MagicMock()
    context_map.model_dump_json.return_value = "{}"

    failing_trace = MagicMock()
    failing_trace.generation.return_value = MagicMock()
    failing_trace.span.side_effect = RuntimeError("langfuse span down")

    with patch.object(
        contract_analysis,
        "_create_langfuse_trace",
        return_value=(MagicMock(), failing_trace),
    ):
        with patch.object(
            contract_analysis,
            "parse_contract_document_with_metadata",
            side_effect=[
                ImageParseResult(text="original text", model="gpt-4o", usage={}),
                ImageParseResult(text="amendment text", model="gpt-4o", usage={}),
            ],
        ):
            with patch.object(contract_analysis, "ContextualizationAgent") as ctx_cls:
                with patch.object(contract_analysis, "ExtractionAgent") as ext_cls:
                    ctx_cls.return_value.run_with_metadata.return_value = MagicMock(
                        context_map=context_map,
                        model="gpt-4o",
                        usage={},
                    )
                    ext_cls.return_value.run_with_metadata.return_value = MagicMock(
                        output=sample_granular_extraction_output(),
                        model="gpt-4o",
                        usage={},
                    )
                    report = run_contract_analysis(
                        analysis_job_id="test-span-job",
                        original_file_path=str(original),
                        amendment_file_path=str(amendment),
                    )

    assert report["validation"]["status"] == "VALID"
    assert failing_trace.span.called


def test_completion_log_includes_metrics(tmp_path, monkeypatch, caplog):
    original, amendment = _write_image_files(tmp_path)

    with caplog.at_level(logging.INFO):
        with _patch_pipeline_agents(
            monkeypatch, extraction_output=sample_granular_extraction_output()
        ):
            run_contract_analysis(
                analysis_job_id="test-log-job",
                original_file_path=str(original),
                amendment_file_path=str(amendment),
            )

    log_text = caplog.text
    assert "validation_status=" in log_text
    assert "warnings_count=" in log_text
    assert "overall_risk_level=" in log_text
    assert "changes=" in log_text
