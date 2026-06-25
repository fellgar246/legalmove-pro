"""Factory for worker job queue providers."""

from __future__ import annotations

from typing import Any

from psycopg import Connection

from config import (
    AWS_REGION,
    SQS_MAX_MESSAGES,
    SQS_QUEUE_URL,
    SQS_VISIBILITY_TIMEOUT,
    SQS_WAIT_TIME_SECONDS,
)
from job_queues.job_queue import JobQueue
from job_queues.postgres_job_queue import PostgresJobQueue
from job_queues.sqs_job_queue import SQSJobQueue


def _build_sqs_client() -> Any:
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError
    except ImportError as exc:
        raise RuntimeError("boto3 is required to use SQS queue provider") from exc

    kwargs: dict[str, str] = {}
    if AWS_REGION:
        kwargs["region_name"] = AWS_REGION

    try:
        return boto3.client("sqs", **kwargs)
    except NoCredentialsError as exc:
        raise RuntimeError(
            "AWS credentials are not available for SQS queue provider"
        ) from exc


def create_job_queue(
    provider: str,
    conn: Connection,
    *,
    sqs_client: Any | None = None,
) -> JobQueue:
    """Build a job queue implementation for the configured provider."""
    normalized = (provider or "postgres").strip().lower()
    if normalized == "postgres":
        return PostgresJobQueue(conn)
    if normalized == "sqs":
        if not SQS_QUEUE_URL:
            raise ValueError("SQS_QUEUE_URL is required when QUEUE_PROVIDER=sqs")
        client = sqs_client or _build_sqs_client()
        return SQSJobQueue(
            conn,
            sqs_client=client,
            queue_url=SQS_QUEUE_URL,
            wait_time_seconds=SQS_WAIT_TIME_SECONDS,
            max_messages=SQS_MAX_MESSAGES,
            visibility_timeout=SQS_VISIBILITY_TIMEOUT,
        )
    raise ValueError(f"Unsupported QUEUE_PROVIDER: {provider}")
