import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import db
import worker
from pipeline.errors import AgentExecutionError


def test_process_job_marks_failed_when_pipeline_raises():
    conn = MagicMock()
    job_id = uuid.uuid4()

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(db, "get_job_document_paths", return_value=("/tmp/o.png", "/tmp/a.png")):
            with patch.object(
                worker,
                "run_contract_analysis",
                side_effect=AgentExecutionError(
                    "OpenAI rate limit reached (HTTP 429). Wait and try again."
                ),
            ):
                with patch.object(db, "mark_failed") as mark_failed:
                    worker.process_job(conn, job_id)
                    mark_failed.assert_called_once_with(
                        conn,
                        job_id,
                        "OpenAI rate limit reached (HTTP 429). Wait and try again.",
                    )


def test_process_job_saves_success_when_pipeline_completes():
    conn = MagicMock()
    job_id = uuid.uuid4()
    report = {"schema_version": "1.0", "validation": {"status": "VALID"}, "changes": []}

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(db, "get_job_document_paths", return_value=("/tmp/o.png", "/tmp/a.png")):
            with patch.object(worker, "run_contract_analysis", return_value=report):
                with patch.object(db, "save_success", return_value="COMPLETED") as save_success:
                    worker.process_job(conn, job_id)
                    save_success.assert_called_once_with(conn, job_id, report)


def test_process_job_uses_mock_result_when_mock_mode_enabled():
    conn = MagicMock()
    job_id = uuid.uuid4()
    mock_report = worker._build_mock_result()

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", True):
        with patch.object(db, "get_job_document_paths", return_value=("/tmp/o.png", "/tmp/a.png")):
            with patch.object(worker, "run_contract_analysis") as run_pipeline:
                with patch.object(db, "save_success", return_value="COMPLETED") as save_success:
                    worker.process_job(conn, job_id)
                    run_pipeline.assert_not_called()
                    save_success.assert_called_once_with(conn, job_id, mock_report)


def test_process_job_marks_failed_on_file_not_found():
    conn = MagicMock()
    job_id = uuid.uuid4()

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(
            db,
            "get_job_document_paths",
            side_effect=FileNotFoundError("Document file not found: missing.png"),
        ):
            with patch.object(db, "mark_failed") as mark_failed:
                worker.process_job(conn, job_id)
                mark_failed.assert_called_once_with(
                    conn,
                    job_id,
                    "Document file not found: missing.png",
                )


def test_process_job_marks_failed_on_invalid_validation_status():
    conn = MagicMock()
    job_id = uuid.uuid4()
    report = {
        "schema_version": "1.0",
        "validation": {"status": "INVALID", "warnings": ["Missing required field."]},
        "changes": [],
    }

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(db, "get_job_document_paths", return_value=("/tmp/o.png", "/tmp/a.png")):
            with patch.object(worker, "run_contract_analysis", return_value=report):
                with patch.object(db, "mark_failed") as mark_failed:
                    with patch.object(db, "save_success") as save_success:
                        worker.process_job(conn, job_id)
                        save_success.assert_not_called()
                        mark_failed.assert_called_once_with(
                            conn,
                            job_id,
                            "Validation failed: Missing required field.",
                        )


def test_process_job_saves_valid_with_warnings_status():
    conn = MagicMock()
    job_id = uuid.uuid4()
    report = {
        "schema_version": "1.0",
        "validation": {"status": "VALID_WITH_WARNINGS", "warnings": ["Low confidence."]},
        "changes": [{"summary": "Review needed.", "risk_level": "MEDIUM"}],
    }

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(db, "get_job_document_paths", return_value=("/tmp/o.png", "/tmp/a.png")):
            with patch.object(worker, "run_contract_analysis", return_value=report):
                with patch.object(db, "save_success", return_value="VALID_WITH_WARNINGS") as save_success:
                    worker.process_job(conn, job_id)
                    save_success.assert_called_once_with(conn, job_id, report)


def test_process_job_marks_failed_with_safe_message_on_unexpected_error():
    conn = MagicMock()
    job_id = uuid.uuid4()

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(db, "get_job_document_paths", return_value=("/tmp/o.png", "/tmp/a.png")):
            with patch.object(worker, "run_contract_analysis", side_effect=KeyError("missing")):
                with patch.object(db, "mark_failed") as mark_failed:
                    worker.process_job(conn, job_id)
                    mark_failed.assert_called_once_with(
                        conn,
                        job_id,
                        "Unexpected worker error. Check worker logs for details.",
                    )
