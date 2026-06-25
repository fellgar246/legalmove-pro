import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import db
from job_queues.sqs_job_queue import SQSJobQueue


def _message(body: str, *, receipt_handle: str = "receipt-1", message_id: str = "msg-1"):
    return {
        "Body": body,
        "ReceiptHandle": receipt_handle,
        "MessageId": message_id,
    }


def test_sqs_job_queue_parses_valid_message_and_claims_job():
    conn = MagicMock()
    job_id = uuid.uuid4()
    sqs_client = MagicMock()
    sqs_client.receive_message.return_value = {
        "Messages": [_message(f'{{"analysis_id":"{job_id}","schema_version":"1.0"}}')],
    }

    with patch.object(db, "get_job_status", return_value="QUEUED"):
        with patch.object(db, "claim_analysis_job_by_id", return_value=True) as claim:
            queue = SQSJobQueue(
                conn,
                sqs_client=sqs_client,
                queue_url="https://sqs.us-east-1.amazonaws.com/123/legalmove-analysis",
            )
            claimed = queue.claim_next_job()

    assert claimed is not None
    assert claimed.analysis_id == str(job_id)
    assert claimed.metadata["sqs_receipt_handle"] == "receipt-1"
    claim.assert_called_once_with(conn, job_id)


def test_sqs_job_queue_deletes_invalid_message():
    conn = MagicMock()
    sqs_client = MagicMock()
    sqs_client.receive_message.return_value = {"Messages": [_message("not-json")]}

    queue = SQSJobQueue(
        conn,
        sqs_client=sqs_client,
        queue_url="https://sqs.us-east-1.amazonaws.com/123/legalmove-analysis",
    )
    claimed = queue.claim_next_job()

    assert claimed is None
    sqs_client.delete_message.assert_called_once()


def test_sqs_job_queue_deletes_message_for_terminal_job():
    conn = MagicMock()
    job_id = uuid.uuid4()
    sqs_client = MagicMock()
    sqs_client.receive_message.return_value = {
        "Messages": [_message(f'{{"analysis_id":"{job_id}","schema_version":"1.0"}}')],
    }

    with patch.object(db, "get_job_status", return_value="COMPLETED"):
        queue = SQSJobQueue(
            conn,
            sqs_client=sqs_client,
            queue_url="https://sqs.us-east-1.amazonaws.com/123/legalmove-analysis",
        )
        claimed = queue.claim_next_job()

    assert claimed is None
    sqs_client.delete_message.assert_called_once()


def test_sqs_job_queue_keeps_message_when_job_not_claimable():
    conn = MagicMock()
    job_id = uuid.uuid4()
    sqs_client = MagicMock()
    sqs_client.receive_message.return_value = {
        "Messages": [_message(f'{{"analysis_id":"{job_id}","schema_version":"1.0"}}')],
    }

    with patch.object(db, "get_job_status", return_value="PROCESSING"):
        with patch.object(db, "claim_analysis_job_by_id", return_value=False):
            queue = SQSJobQueue(
                conn,
                sqs_client=sqs_client,
                queue_url="https://sqs.us-east-1.amazonaws.com/123/legalmove-analysis",
            )
            claimed = queue.claim_next_job()

    assert claimed is None
    sqs_client.delete_message.assert_not_called()


def test_sqs_job_queue_mark_completed_deletes_message():
    conn = MagicMock()
    job_id = uuid.uuid4()
    sqs_client = MagicMock()
    queue = SQSJobQueue(
        conn,
        sqs_client=sqs_client,
        queue_url="https://sqs.us-east-1.amazonaws.com/123/legalmove-analysis",
    )
    from job_queues.job_queue import ClaimedAnalysisJob

    claimed = ClaimedAnalysisJob(
        analysis_id=str(job_id),
        metadata={"sqs_receipt_handle": "receipt-1"},
    )
    result = {"schema_version": "1.0", "validation": {"status": "VALID"}, "changes": []}

    with patch.object(db, "save_success", return_value="COMPLETED"):
        status = queue.mark_completed(claimed, result)

    assert status == "COMPLETED"
    sqs_client.delete_message.assert_called_once_with(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/123/legalmove-analysis",
        ReceiptHandle="receipt-1",
    )


def test_sqs_job_queue_mark_failed_deletes_message():
    conn = MagicMock()
    job_id = uuid.uuid4()
    sqs_client = MagicMock()
    queue = SQSJobQueue(
        conn,
        sqs_client=sqs_client,
        queue_url="https://sqs.us-east-1.amazonaws.com/123/legalmove-analysis",
    )
    from job_queues.job_queue import ClaimedAnalysisJob

    claimed = ClaimedAnalysisJob(
        analysis_id=str(job_id),
        metadata={"sqs_receipt_handle": "receipt-1"},
    )

    with patch.object(db, "mark_failed") as mark_failed:
        queue.mark_failed(claimed, "pipeline failed")

    mark_failed.assert_called_once_with(conn, job_id, "pipeline failed")
    sqs_client.delete_message.assert_called_once()
