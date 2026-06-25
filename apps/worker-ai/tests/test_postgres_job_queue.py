import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import db
from job_queues.job_queue import ClaimedAnalysisJob
from job_queues.postgres_job_queue import PostgresJobQueue
from storage.document_materializer import DocumentStorageRef


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


def test_postgres_job_queue_claim_next_job_returns_claimed_job():
    conn = MagicMock()
    job_id = uuid.uuid4()
    queue = PostgresJobQueue(conn)

    with patch.object(db, "claim_next_job", return_value=job_id) as claim_next_job:
        claimed = queue.claim_next_job()

    claim_next_job.assert_called_once_with(conn)
    assert claimed == ClaimedAnalysisJob(analysis_id=str(job_id), status="PROCESSING")


def test_postgres_job_queue_claim_next_job_returns_none_when_empty():
    conn = MagicMock()
    queue = PostgresJobQueue(conn)

    with patch.object(db, "claim_next_job", return_value=None):
        assert queue.claim_next_job() is None


def test_postgres_job_queue_get_job_document_refs_delegates_to_db():
    conn = MagicMock()
    queue = PostgresJobQueue(conn)
    job = ClaimedAnalysisJob(analysis_id=str(uuid.uuid4()))

    with patch.object(db, "get_job_document_refs", return_value=_document_refs()) as get_refs:
        refs = queue.get_job_document_refs(job)

    get_refs.assert_called_once_with(conn, uuid.UUID(job.analysis_id))
    assert refs == _document_refs()


def test_postgres_job_queue_mark_completed_delegates_to_db():
    conn = MagicMock()
    queue = PostgresJobQueue(conn)
    job = ClaimedAnalysisJob(analysis_id=str(uuid.uuid4()))
    result = {"schema_version": "1.0", "validation": {"status": "VALID"}, "changes": []}

    with patch.object(db, "save_success", return_value="COMPLETED") as save_success:
        status = queue.mark_completed(job, result)

    save_refs = save_success.call_args[0]
    assert save_refs[0] is conn
    assert save_refs[1] == uuid.UUID(job.analysis_id)
    assert save_refs[2] == result
    assert status == "COMPLETED"


def test_postgres_job_queue_mark_failed_delegates_to_db():
    conn = MagicMock()
    queue = PostgresJobQueue(conn)
    job = ClaimedAnalysisJob(analysis_id=str(uuid.uuid4()))

    with patch.object(db, "mark_failed") as mark_failed:
        queue.mark_failed(job, "Pipeline failed")

    mark_failed.assert_called_once_with(conn, uuid.UUID(job.analysis_id), "Pipeline failed")


def test_postgres_job_queue_mark_needs_review_delegates_to_save_success():
    conn = MagicMock()
    queue = PostgresJobQueue(conn)
    job = ClaimedAnalysisJob(analysis_id=str(uuid.uuid4()))
    result = {
        "schema_version": "1.0",
        "validation": {"status": "VALID_WITH_WARNINGS"},
        "changes": [],
    }

    with patch.object(db, "save_success", return_value="VALID_WITH_WARNINGS") as save_success:
        status = queue.mark_needs_review(job, result, reason="Low confidence")

    save_success.assert_called_once_with(conn, uuid.UUID(job.analysis_id), result)
    assert status == "VALID_WITH_WARNINGS"
