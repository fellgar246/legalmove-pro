import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import db
from job_queues.azure_service_bus_job_queue import AzureServiceBusJobQueue


def _message(body: str):
    message = MagicMock()
    message.body = body.encode("utf-8")
    return message


def test_azure_service_bus_job_queue_parses_valid_message_and_claims_job():
    conn = MagicMock()
    job_id = uuid.uuid4()
    receiver = MagicMock()
    receiver.receive_messages.return_value = [
        _message(f'{{"analysis_id":"{job_id}","schema_version":"1.0"}}')
    ]

    with patch.object(db, "get_job_status", return_value="QUEUED"):
        with patch.object(db, "claim_analysis_job_by_id", return_value=True) as claim:
            queue = AzureServiceBusJobQueue(conn, receiver=receiver)
            claimed = queue.claim_next_job()

    assert claimed is not None
    assert claimed.analysis_id == str(job_id)
    claim.assert_called_once_with(conn, job_id)


def _message_generator_body(body: str):
    """Mimic azure-servicebus returning the AMQP data body as a byte-chunk generator."""
    message = MagicMock()
    encoded = body.encode("utf-8")
    message.body = (chunk for chunk in (encoded[:5], encoded[5:]))
    return message


def test_azure_service_bus_job_queue_parses_generator_body_and_claims_job():
    conn = MagicMock()
    job_id = uuid.uuid4()
    receiver = MagicMock()
    receiver.receive_messages.return_value = [
        _message_generator_body(f'{{"analysis_id":"{job_id}","schema_version":"1.0"}}')
    ]

    with patch.object(db, "get_job_status", return_value="QUEUED"):
        with patch.object(db, "claim_analysis_job_by_id", return_value=True) as claim:
            queue = AzureServiceBusJobQueue(conn, receiver=receiver)
            claimed = queue.claim_next_job()

    assert claimed is not None
    assert claimed.analysis_id == str(job_id)
    claim.assert_called_once_with(conn, job_id)


def test_azure_service_bus_job_queue_completes_invalid_message():
    conn = MagicMock()
    receiver = MagicMock()
    receiver.receive_messages.return_value = [_message("not-json")]

    queue = AzureServiceBusJobQueue(conn, receiver=receiver)
    claimed = queue.claim_next_job()

    assert claimed is None
    receiver.complete_message.assert_called_once()


def test_azure_service_bus_job_queue_completes_message_for_terminal_job():
    conn = MagicMock()
    job_id = uuid.uuid4()
    receiver = MagicMock()
    receiver.receive_messages.return_value = [
        _message(f'{{"analysis_id":"{job_id}","schema_version":"1.0"}}')
    ]

    with patch.object(db, "get_job_status", return_value="COMPLETED"):
        queue = AzureServiceBusJobQueue(conn, receiver=receiver)
        claimed = queue.claim_next_job()

    assert claimed is None
    receiver.complete_message.assert_called_once()


def test_azure_service_bus_job_queue_abandons_message_when_job_not_claimable():
    conn = MagicMock()
    job_id = uuid.uuid4()
    receiver = MagicMock()
    receiver.receive_messages.return_value = [
        _message(f'{{"analysis_id":"{job_id}","schema_version":"1.0"}}')
    ]

    with patch.object(db, "get_job_status", return_value="PROCESSING"):
        with patch.object(db, "claim_analysis_job_by_id", return_value=False):
            queue = AzureServiceBusJobQueue(conn, receiver=receiver)
            claimed = queue.claim_next_job()

    assert claimed is None
    receiver.abandon_message.assert_called_once()
    receiver.complete_message.assert_not_called()


def test_azure_service_bus_job_queue_mark_completed_completes_message():
    conn = MagicMock()
    job_id = uuid.uuid4()
    receiver = MagicMock()
    message = _message(f'{{"analysis_id":"{job_id}"}}')
    queue = AzureServiceBusJobQueue(conn, receiver=receiver)
    from job_queues.job_queue import ClaimedAnalysisJob

    claimed = ClaimedAnalysisJob(
        analysis_id=str(job_id),
        metadata={"service_bus_message": message, "service_bus_receiver": receiver},
    )
    result = {"schema_version": "1.0", "validation": {"status": "VALID"}, "changes": []}

    with patch.object(db, "save_success", return_value="COMPLETED"):
        status = queue.mark_completed(claimed, result)

    assert status == "COMPLETED"
    receiver.complete_message.assert_called_once_with(message)
