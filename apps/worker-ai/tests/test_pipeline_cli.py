import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pipeline.cli import main
from pipeline.errors import DocumentLoadError


SAMPLE_REPORT = {
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
    "validation": {"status": "VALID", "warnings": []},
}


def test_cli_prints_json_and_saves_output(tmp_path, monkeypatch):
    output_file = tmp_path / "outputs" / "local-test-001.result.json"
    monkeypatch.setattr("pipeline.cli._WORKER_AI_ROOT", tmp_path)

    argv = [
        "--analysis-job-id",
        "local-test-001",
        "--original-file-path",
        str(tmp_path / "original.png"),
        "--amendment-file-path",
        str(tmp_path / "amendment.png"),
        "--save",
    ]

    with patch("pipeline.cli.validate_openai_config"):
        with patch("pipeline.cli.run_contract_analysis", return_value=SAMPLE_REPORT):
            exit_code = main(argv)

    assert exit_code == 0
    assert output_file.exists()
    saved = json.loads(output_file.read_text(encoding="utf-8"))
    assert saved["schema_version"] == "1.0"


def test_cli_returns_error_on_pipeline_failure(capsys):
    argv = [
        "--original-file-path",
        "/tmp/original.png",
        "--amendment-file-path",
        "/tmp/amendment.png",
    ]

    with patch("pipeline.cli.validate_openai_config"):
        with patch(
            "pipeline.cli.run_contract_analysis",
            side_effect=DocumentLoadError("Document file not found (original): /tmp/original.png"),
        ):
            exit_code = main(argv)

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Document file not found (original)" in captured.err


def test_cli_returns_error_on_unexpected_failure(capsys):
    argv = [
        "--original-file-path",
        "/tmp/original.png",
        "--amendment-file-path",
        "/tmp/amendment.png",
    ]

    with patch("pipeline.cli.validate_openai_config"):
        with patch("pipeline.cli.run_contract_analysis", side_effect=RuntimeError("boom")):
            exit_code = main(argv)

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.err.strip() == "Pipeline CLI failed. Check logs for details."


def test_cli_does_not_require_database_url(monkeypatch):
    import config

    monkeypatch.setattr(config, "DATABASE_URL", "")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")

    argv = [
        "--original-file-path",
        "/tmp/original.png",
        "--amendment-file-path",
        "/tmp/amendment.png",
    ]

    stdout = StringIO()
    with patch("sys.stdout", stdout):
        with patch("pipeline.cli.run_contract_analysis", return_value=SAMPLE_REPORT):
            exit_code = main(argv)

    assert exit_code == 0
    report = json.loads(stdout.getvalue())
    assert report["schema_version"] == "1.0"
