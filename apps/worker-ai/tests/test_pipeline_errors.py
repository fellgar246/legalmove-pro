import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.extraction_models import GranularContractChangeOutput
from core.image_parser import ImageParseResult
from pipeline import contract_analysis
from pipeline.contract_analysis import run_contract_analysis
from pipeline.errors import DocumentLoadError, PipelineError
from tests.fixtures import sample_granular_extraction_output


def test_run_contract_analysis_raises_when_original_missing(tmp_path):
    amendment = tmp_path / "amend.png"
    amendment.write_bytes(b"x")

    with pytest.raises(DocumentLoadError, match="Document file not found \\(original\\)"):
        run_contract_analysis(
            analysis_job_id="test-job",
            original_file_path=str(tmp_path / "missing.png"),
            amendment_file_path=str(amendment),
        )


def test_run_contract_analysis_raises_when_openai_key_missing(tmp_path, monkeypatch):
    original = tmp_path / "orig.png"
    amendment = tmp_path / "amend.png"
    original.write_bytes(b"x")
    amendment.write_bytes(b"x")

    import config

    monkeypatch.setattr(config, "OPENAI_API_KEY", "")

    with pytest.raises(PipelineError, match="OPENAI_API_KEY is required to run the AI pipeline"):
        run_contract_analysis(
            analysis_job_id="test-job",
            original_file_path=str(original),
            amendment_file_path=str(amendment),
        )


def test_run_contract_analysis_continues_when_langfuse_trace_fails(tmp_path, monkeypatch):
    original = tmp_path / "orig.png"
    amendment = tmp_path / "amend.png"
    original.write_bytes(b"x")
    amendment.write_bytes(b"x")

    monkeypatch.setattr(contract_analysis, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(contract_analysis, "langfuse_enabled", lambda: True)

    mock_report = {
        "schema_version": "1.0",
        "disclaimer": "AI-generated review support. Not legal advice.",
        "analysis_summary": {
            "executive_summary": "Test summary",
            "overall_risk_level": "MEDIUM",
            "total_changes": 1,
            "high_risk_changes": 0,
            "requires_human_review": True,
        },
        "changes": [],
        "risks": [],
        "human_review_recommendations": [],
        "validation": {"status": "VALID", "warnings": []},
    }

    context_map = MagicMock()
    context_map.model_dump_json.return_value = "{}"

    with patch.object(contract_analysis, "_build_langfuse_client", side_effect=RuntimeError("langfuse down")):
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
                    with patch.object(
                        contract_analysis,
                        "map_extraction_to_final_report",
                        return_value=mock_report,
                    ):
                        report = run_contract_analysis(
                            analysis_job_id="test-job",
                            original_file_path=str(original),
                            amendment_file_path=str(amendment),
                        )

    assert report["disclaimer"] == mock_report["disclaimer"]
    assert report["schema_version"] == "1.0"
