"""Factory for worker job queue providers."""

from __future__ import annotations

from typing import Any

from psycopg import Connection

from config import (
    AWS_REGION,
    AZURE_CLIENT_ID,
    AZURE_SERVICE_BUS_NAMESPACE,
    AZURE_SERVICE_BUS_QUEUE_NAME,
    AZURE_SERVICE_BUS_WAIT_TIME_SECONDS,
    AZURE_STORAGE_ACCOUNT_NAME,
    AZURE_STORAGE_CONTAINER_NAME,
    SQS_MAX_MESSAGES,
    SQS_QUEUE_URL,
    SQS_VISIBILITY_TIMEOUT,
    SQS_WAIT_TIME_SECONDS,
)
from job_queues.azure_service_bus_job_queue import AzureServiceBusJobQueue
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


def _build_service_bus_receiver() -> Any:
    try:
        from azure.identity import DefaultAzureCredential
        from azure.servicebus import ServiceBusClient
    except ImportError as exc:
        raise RuntimeError(
            "azure-servicebus and azure-identity are required to use azure_service_bus queue provider"
        ) from exc

    if not AZURE_SERVICE_BUS_NAMESPACE:
        raise ValueError(
            "AZURE_SERVICE_BUS_NAMESPACE is required when QUEUE_PROVIDER=azure_service_bus"
        )
    if not AZURE_SERVICE_BUS_QUEUE_NAME:
        raise ValueError(
            "AZURE_SERVICE_BUS_QUEUE_NAME is required when QUEUE_PROVIDER=azure_service_bus"
        )

    credential_kwargs: dict[str, str] = {}
    if AZURE_CLIENT_ID:
        credential_kwargs["managed_identity_client_id"] = AZURE_CLIENT_ID

    credential = DefaultAzureCredential(**credential_kwargs)
    client = ServiceBusClient(
        fully_qualified_namespace=f"{AZURE_SERVICE_BUS_NAMESPACE}.servicebus.windows.net",
        credential=credential,
    )
    return client.get_queue_receiver(queue_name=AZURE_SERVICE_BUS_QUEUE_NAME)


def create_job_queue(
    provider: str,
    conn: Connection,
    *,
    sqs_client: Any | None = None,
    service_bus_receiver: Any | None = None,
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
    if normalized == "azure_service_bus":
        if not AZURE_SERVICE_BUS_NAMESPACE:
            raise ValueError(
                "AZURE_SERVICE_BUS_NAMESPACE is required when QUEUE_PROVIDER=azure_service_bus"
            )
        if not AZURE_SERVICE_BUS_QUEUE_NAME:
            raise ValueError(
                "AZURE_SERVICE_BUS_QUEUE_NAME is required when QUEUE_PROVIDER=azure_service_bus"
            )
        receiver = service_bus_receiver or _build_service_bus_receiver()
        return AzureServiceBusJobQueue(
            conn,
            receiver=receiver,
            max_wait_time=float(AZURE_SERVICE_BUS_WAIT_TIME_SECONDS),
            max_message_count=SQS_MAX_MESSAGES,
        )
    raise ValueError(f"Unsupported QUEUE_PROVIDER: {provider}")
