import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from job_queues.factory import create_job_queue
from job_queues.postgres_job_queue import PostgresJobQueue
from job_queues.sqs_job_queue import SQSJobQueue


def test_create_job_queue_defaults_to_postgres():
    conn = MagicMock()
    queue = create_job_queue("", conn)
    assert isinstance(queue, PostgresJobQueue)


def test_create_job_queue_uses_postgres_provider():
    conn = MagicMock()
    queue = create_job_queue("postgres", conn)
    assert isinstance(queue, PostgresJobQueue)


def test_create_job_queue_uses_sqs_provider_with_mock_client(monkeypatch):
    conn = MagicMock()
    import job_queues.factory as factory_module

    monkeypatch.setattr(
        factory_module,
        "SQS_QUEUE_URL",
        "https://sqs.us-east-1.amazonaws.com/123/legalmove-analysis",
    )

    sqs_client = MagicMock()
    queue = create_job_queue("sqs", conn, sqs_client=sqs_client)
    assert isinstance(queue, SQSJobQueue)


def test_create_job_queue_fails_for_sqs_without_queue_url(monkeypatch):
    conn = MagicMock()
    import job_queues.factory as factory_module

    monkeypatch.setattr(factory_module, "SQS_QUEUE_URL", "")
    with pytest.raises(ValueError, match="SQS_QUEUE_URL is required"):
        create_job_queue("sqs", conn, sqs_client=MagicMock())


def test_create_job_queue_fails_for_unknown_provider():
    conn = MagicMock()
    with pytest.raises(ValueError, match="Unsupported QUEUE_PROVIDER: gcs"):
        create_job_queue("gcs", conn)
