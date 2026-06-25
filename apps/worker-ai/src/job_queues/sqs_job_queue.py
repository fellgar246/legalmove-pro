"""AWS SQS-backed job queue for analysis dispatch."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from psycopg import Connection

import db
from job_queues.job_queue import ClaimedAnalysisJob, JobQueue
from storage.document_materializer import DocumentStorageRef

logger = logging.getLogger(__name__)

_METADATA_RECEIPT_HANDLE = "sqs_receipt_handle"
_METADATA_MESSAGE_ID = "sqs_message_id"


class SQSJobQueue(JobQueue):
    """Consume analysis jobs from SQS and persist lifecycle in PostgreSQL."""

    def __init__(
        self,
        conn: Connection,
        *,
        sqs_client: Any,
        queue_url: str,
        wait_time_seconds: int = 10,
        max_messages: int = 1,
        visibility_timeout: int | None = None,
    ) -> None:
        self._conn = conn
        self._sqs_client = sqs_client
        self._queue_url = queue_url.strip()
        self._wait_time_seconds = wait_time_seconds
        self._max_messages = max_messages
        self._visibility_timeout = visibility_timeout

    def claim_next_job(self) -> ClaimedAnalysisJob | None:
        receive_kwargs: dict[str, Any] = {
            "QueueUrl": self._queue_url,
            "MaxNumberOfMessages": self._max_messages,
            "WaitTimeSeconds": self._wait_time_seconds,
            "MessageAttributeNames": ["All"],
        }
        if self._visibility_timeout is not None:
            receive_kwargs["VisibilityTimeout"] = self._visibility_timeout

        try:
            response = self._sqs_client.receive_message(**receive_kwargs)
        except Exception as exc:
            raise RuntimeError("Failed to receive SQS message") from exc

        messages = response.get("Messages") or []
        if not messages:
            return None

        message = messages[0]
        receipt_handle = message.get("ReceiptHandle")
        message_id = message.get("MessageId")
        body = message.get("Body", "")

        if not receipt_handle:
            logger.warning("[sqs] received message without receipt handle; skipping")
            return None

        analysis_id = self._parse_analysis_id(body)
        if analysis_id is None:
            logger.warning("[sqs] invalid message body; deleting message")
            self._delete_message(receipt_handle)
            return None

        try:
            job_uuid = uuid.UUID(analysis_id)
        except ValueError:
            logger.warning("[sqs] invalid analysis_id %r; deleting message", analysis_id)
            self._delete_message(receipt_handle)
            return None

        status = db.get_job_status(self._conn, job_uuid)
        if status is None:
            logger.warning("[sqs] analysis job %s not found; deleting message", analysis_id)
            self._delete_message(receipt_handle)
            return None

        if status in db.TERMINAL_JOB_STATUSES:
            logger.info("[sqs] analysis job %s already terminal (%s); deleting message", analysis_id, status)
            self._delete_message(receipt_handle)
            return None

        if not db.claim_analysis_job_by_id(self._conn, job_uuid):
            logger.info(
                "[sqs] analysis job %s not claimable (status=%s); keeping message",
                analysis_id,
                status,
            )
            return None

        return ClaimedAnalysisJob(
            analysis_id=analysis_id,
            status="PROCESSING",
            metadata={
                _METADATA_RECEIPT_HANDLE: receipt_handle,
                _METADATA_MESSAGE_ID: message_id,
            },
        )

    def get_job_document_refs(
        self, job: ClaimedAnalysisJob
    ) -> tuple[DocumentStorageRef, DocumentStorageRef]:
        job_id = uuid.UUID(job.analysis_id)
        return db.get_job_document_refs(self._conn, job_id)

    def mark_completed(self, job: ClaimedAnalysisJob, result: dict[str, Any]) -> str:
        job_id = uuid.UUID(job.analysis_id)
        status = db.save_success(self._conn, job_id, result)
        self._delete_message_from_job(job)
        return status

    def mark_failed(self, job: ClaimedAnalysisJob, error_message: str) -> None:
        job_id = uuid.UUID(job.analysis_id)
        db.mark_failed(self._conn, job_id, error_message)
        self._delete_message_from_job(job)

    def mark_needs_review(
        self,
        job: ClaimedAnalysisJob,
        result: dict[str, Any],
        reason: str | None = None,
    ) -> str:
        return self.mark_completed(job, result)

    def _parse_analysis_id(self, body: str) -> str | None:
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, dict):
            return None

        analysis_id = payload.get("analysis_id")
        if analysis_id is None:
            return None

        normalized = str(analysis_id).strip()
        return normalized or None

    def _delete_message_from_job(self, job: ClaimedAnalysisJob) -> None:
        metadata = job.metadata or {}
        receipt_handle = metadata.get(_METADATA_RECEIPT_HANDLE)
        if not receipt_handle:
            return
        self._delete_message(receipt_handle)

    def _delete_message(self, receipt_handle: str) -> None:
        try:
            self._sqs_client.delete_message(
                QueueUrl=self._queue_url,
                ReceiptHandle=receipt_handle,
            )
        except Exception as exc:
            logger.warning("[sqs] failed to delete message: %s", exc)
