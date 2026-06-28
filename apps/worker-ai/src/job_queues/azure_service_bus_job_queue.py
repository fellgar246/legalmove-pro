"""Azure Service Bus-backed job queue for analysis dispatch."""

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

_METADATA_MESSAGE = "service_bus_message"
_METADATA_RECEIVER = "service_bus_receiver"


class AzureServiceBusJobQueue(JobQueue):
    """Consume analysis jobs from Azure Service Bus and persist lifecycle in PostgreSQL."""

    def __init__(
        self,
        conn: Connection,
        *,
        receiver: Any,
        max_wait_time: float = 10.0,
        max_message_count: int = 1,
    ) -> None:
        self._conn = conn
        self._receiver = receiver
        self._max_wait_time = max_wait_time
        self._max_message_count = max_message_count

    def claim_next_job(self) -> ClaimedAnalysisJob | None:
        try:
            messages = self._receiver.receive_messages(
                max_message_count=self._max_message_count,
                max_wait_time=self._max_wait_time,
            )
        except Exception as exc:
            raise RuntimeError("Failed to receive Service Bus message") from exc

        message_list = list(messages)
        if not message_list:
            return None

        message = message_list[0]
        body = self._message_body(message)

        analysis_id = self._parse_analysis_id(body)
        if analysis_id is None:
            logger.warning("[servicebus] invalid message body; completing message")
            self._complete_message(message)
            return None

        try:
            job_uuid = uuid.UUID(analysis_id)
        except ValueError:
            logger.warning("[servicebus] invalid analysis_id %r; completing message", analysis_id)
            self._complete_message(message)
            return None

        status = db.get_job_status(self._conn, job_uuid)
        if status is None:
            logger.warning(
                "[servicebus] analysis job %s not found; completing message",
                analysis_id,
            )
            self._complete_message(message)
            return None

        if status in db.TERMINAL_JOB_STATUSES:
            logger.info(
                "[servicebus] analysis job %s already terminal (%s); completing message",
                analysis_id,
                status,
            )
            self._complete_message(message)
            return None

        if not db.claim_analysis_job_by_id(self._conn, job_uuid):
            logger.info(
                "[servicebus] analysis job %s not claimable (status=%s); abandoning message",
                analysis_id,
                status,
            )
            self._abandon_message(message)
            return None

        return ClaimedAnalysisJob(
            analysis_id=analysis_id,
            status="PROCESSING",
            metadata={
                _METADATA_MESSAGE: message,
                _METADATA_RECEIVER: self._receiver,
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
        self._complete_message_from_job(job)
        return status

    def mark_failed(self, job: ClaimedAnalysisJob, error_message: str) -> None:
        job_id = uuid.UUID(job.analysis_id)
        db.mark_failed(self._conn, job_id, error_message)
        self._complete_message_from_job(job)

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

    def _message_body(self, message: Any) -> str:
        raw = getattr(message, "body", b"")
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        if isinstance(raw, str):
            return raw
        # azure-servicebus returns a generator of byte chunks for AMQP data bodies.
        try:
            chunks = list(raw)
        except TypeError:
            return str(raw)
        parts: list[bytes] = []
        for chunk in chunks:
            if isinstance(chunk, bytes):
                parts.append(chunk)
            elif isinstance(chunk, str):
                parts.append(chunk.encode("utf-8"))
            else:
                parts.append(str(chunk).encode("utf-8"))
        return b"".join(parts).decode("utf-8")

    def _complete_message_from_job(self, job: ClaimedAnalysisJob) -> None:
        metadata = job.metadata or {}
        message = metadata.get(_METADATA_MESSAGE)
        if message is None:
            return
        self._complete_message(message)

    def _complete_message(self, message: Any) -> None:
        try:
            self._receiver.complete_message(message)
        except Exception as exc:
            logger.warning("[servicebus] failed to complete message: %s", exc)

    def _abandon_message(self, message: Any) -> None:
        try:
            self._receiver.abandon_message(message)
        except Exception as exc:
            logger.warning("[servicebus] failed to abandon message: %s", exc)
