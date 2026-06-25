import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import worker
from pipeline.errors import AgentExecutionError
from job_queues.job_queue import ClaimedAnalysisJob, JobQueue
from storage.document_materializer import DocumentStorageRef, MaterializedDocument


def _document_refs() -> tuple[DocumentStorageRef, DocumentStorageRef]:
    return (
        DocumentStorageRef(
            document_id="orig",
            storage_provider="local",
            storage_path="/tmp/o.png",
            storage_key="o.png",
            original_filename="o.png",
            content_type="image/png",
        ),
        DocumentStorageRef(
            document_id="amend",
            storage_provider="local",
            storage_path="/tmp/a.png",
            storage_key="a.png",
            original_filename="a.png",
            content_type="image/png",
        ),
    )


def _claimed_job() -> ClaimedAnalysisJob:
    return ClaimedAnalysisJob(analysis_id=str(uuid.uuid4()), status="PROCESSING")


class FakeJobQueue(JobQueue):
    def __init__(self) -> None:
        self.mark_failed_calls: list[tuple[ClaimedAnalysisJob, str]] = []
        self.mark_completed_calls: list[tuple[ClaimedAnalysisJob, dict]] = []
        self.mark_needs_review_calls: list[tuple[ClaimedAnalysisJob, dict, str | None]] = []

    def claim_next_job(self) -> ClaimedAnalysisJob | None:
        return None

    def get_job_document_refs(
        self, job: ClaimedAnalysisJob
    ) -> tuple[DocumentStorageRef, DocumentStorageRef]:
        return _document_refs()

    def mark_completed(self, job: ClaimedAnalysisJob, result: dict) -> str:
        self.mark_completed_calls.append((job, result))
        return "COMPLETED"

    def mark_failed(self, job: ClaimedAnalysisJob, error_message: str) -> None:
        self.mark_failed_calls.append((job, error_message))

    def mark_needs_review(
        self,
        job: ClaimedAnalysisJob,
        result: dict,
        reason: str | None = None,
    ) -> str:
        self.mark_needs_review_calls.append((job, result, reason))
        return "VALID_WITH_WARNINGS"


def test_process_job_marks_failed_when_pipeline_raises():
    job_queue = FakeJobQueue()
    job = _claimed_job()

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(
            worker,
            "_materialize_job_documents",
            return_value=(
                [
                    MaterializedDocument(local_path="/tmp/o.png", should_cleanup=False),
                    MaterializedDocument(local_path="/tmp/a.png", should_cleanup=False),
                ],
                "/tmp/o.png",
                "/tmp/a.png",
            ),
        ):
            with patch.object(
                worker,
                "run_contract_analysis",
                side_effect=AgentExecutionError(
                    "OpenAI rate limit reached (HTTP 429). Wait and try again."
                ),
            ):
                with patch.object(worker, "_cleanup_materialized_documents") as cleanup:
                    worker.process_job(job_queue, job)
                    assert job_queue.mark_failed_calls == [
                        (
                            job,
                            "OpenAI rate limit reached (HTTP 429). Wait and try again.",
                        )
                    ]
                    cleanup.assert_called_once()


def test_process_job_saves_success_when_pipeline_completes():
    job_queue = FakeJobQueue()
    job = _claimed_job()
    report = {"schema_version": "1.0", "validation": {"status": "VALID"}, "changes": []}
    materialized = [
        MaterializedDocument(local_path="/tmp/o.png", should_cleanup=False),
        MaterializedDocument(local_path="/tmp/a.png", should_cleanup=False),
    ]

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(
            worker,
            "_materialize_job_documents",
            return_value=(materialized, "/tmp/o.png", "/tmp/a.png"),
        ):
            with patch.object(worker, "run_contract_analysis", return_value=report):
                with patch.object(worker, "_cleanup_materialized_documents") as cleanup:
                    worker.process_job(job_queue, job)
                    assert job_queue.mark_completed_calls == [(job, report)]
                    cleanup.assert_called_once_with(materialized)


def test_process_job_uses_mock_result_when_mock_mode_enabled():
    job_queue = FakeJobQueue()
    job = _claimed_job()
    mock_report = worker._build_mock_result()
    materialized = [
        MaterializedDocument(local_path="/tmp/o.png", should_cleanup=False),
        MaterializedDocument(local_path="/tmp/a.png", should_cleanup=False),
    ]

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", True):
        with patch.object(
            worker,
            "_materialize_job_documents",
            return_value=(materialized, "/tmp/o.png", "/tmp/a.png"),
        ):
            with patch.object(worker, "run_contract_analysis") as run_pipeline:
                with patch.object(worker, "_cleanup_materialized_documents") as cleanup:
                    worker.process_job(job_queue, job)
                    run_pipeline.assert_not_called()
                    assert job_queue.mark_completed_calls == [(job, mock_report)]
                    cleanup.assert_called_once_with(materialized)


def test_process_job_marks_failed_on_materialization_error():
    job_queue = FakeJobQueue()
    job = _claimed_job()

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(
            worker,
            "_materialize_job_documents",
            side_effect=FileNotFoundError("Document file not found: missing.png"),
        ):
            with patch.object(worker, "_cleanup_materialized_documents") as cleanup:
                worker.process_job(job_queue, job)
                assert job_queue.mark_failed_calls == [
                    (job, "Document file not found: missing.png")
                ]
                cleanup.assert_called_once_with([])


def test_process_job_marks_failed_on_invalid_validation_status():
    job_queue = FakeJobQueue()
    job = _claimed_job()
    report = {
        "schema_version": "1.0",
        "validation": {"status": "INVALID", "warnings": ["Missing required field."]},
        "changes": [],
    }
    materialized = [
        MaterializedDocument(local_path="/tmp/o.png", should_cleanup=False),
        MaterializedDocument(local_path="/tmp/a.png", should_cleanup=False),
    ]

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(
            worker,
            "_materialize_job_documents",
            return_value=(materialized, "/tmp/o.png", "/tmp/a.png"),
        ):
            with patch.object(worker, "run_contract_analysis", return_value=report):
                with patch.object(worker, "_cleanup_materialized_documents") as cleanup:
                    worker.process_job(job_queue, job)
                    assert job_queue.mark_completed_calls == []
                    assert job_queue.mark_failed_calls == [
                        (job, "Validation failed: Missing required field.")
                    ]
                    cleanup.assert_called_once_with(materialized)


def test_process_job_saves_valid_with_warnings_status():
    job_queue = FakeJobQueue()
    job = _claimed_job()
    report = {
        "schema_version": "1.0",
        "validation": {"status": "VALID_WITH_WARNINGS", "warnings": ["Low confidence."]},
        "changes": [{"summary": "Review needed.", "risk_level": "MEDIUM"}],
    }
    materialized = [
        MaterializedDocument(local_path="/tmp/o.png", should_cleanup=False),
        MaterializedDocument(local_path="/tmp/a.png", should_cleanup=False),
    ]

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(
            worker,
            "_materialize_job_documents",
            return_value=(materialized, "/tmp/o.png", "/tmp/a.png"),
        ):
            with patch.object(worker, "run_contract_analysis", return_value=report):
                with patch.object(worker, "_cleanup_materialized_documents") as cleanup:
                    worker.process_job(job_queue, job)
                    assert job_queue.mark_needs_review_calls == [(job, report, None)]
                    cleanup.assert_called_once_with(materialized)


def test_process_job_marks_failed_with_safe_message_on_unexpected_error():
    job_queue = FakeJobQueue()
    job = _claimed_job()
    materialized = [
        MaterializedDocument(local_path="/tmp/o.png", should_cleanup=False),
        MaterializedDocument(local_path="/tmp/a.png", should_cleanup=False),
    ]

    with patch.object(worker, "WORKER_USE_MOCK_RESULT", False):
        with patch.object(
            worker,
            "_materialize_job_documents",
            return_value=(materialized, "/tmp/o.png", "/tmp/a.png"),
        ):
            with patch.object(worker, "run_contract_analysis", side_effect=KeyError("missing")):
                with patch.object(worker, "_cleanup_materialized_documents") as cleanup:
                    worker.process_job(job_queue, job)
                    assert job_queue.mark_failed_calls == [
                        (
                            job,
                            "Unexpected worker error. Check worker logs for details.",
                        )
                    ]
                    cleanup.assert_called_once_with(materialized)


def test_run_once_processes_claimed_job():
    job = _claimed_job()

    class ClaimingQueue(FakeJobQueue):
        def claim_next_job(self) -> ClaimedAnalysisJob | None:
            return job

    job_queue = ClaimingQueue()

    with patch.object(worker, "process_job") as process_job:
        worker.run_once(job_queue)
        process_job.assert_called_once_with(job_queue, job)


def test_run_once_noops_when_queue_is_empty():
    job_queue = FakeJobQueue()

    with patch.object(worker, "process_job") as process_job:
        worker.run_once(job_queue)
        process_job.assert_not_called()
