"""PostgreSQL-backed job queue using existing db.py helpers."""

from __future__ import annotations

import uuid
from typing import Any

from psycopg import Connection

import db
from job_queues.job_queue import ClaimedAnalysisJob, JobQueue
from storage.document_materializer import DocumentStorageRef


class PostgresJobQueue(JobQueue):
    """Claim and update analysis jobs via PostgreSQL polling."""

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def claim_next_job(self) -> ClaimedAnalysisJob | None:
        job_id = db.claim_next_job(self._conn)
        if job_id is None:
            return None
        return ClaimedAnalysisJob(
            analysis_id=str(job_id),
            status="PROCESSING",
        )

    def get_job_document_refs(
        self, job: ClaimedAnalysisJob
    ) -> tuple[DocumentStorageRef, DocumentStorageRef]:
        job_id = uuid.UUID(job.analysis_id)
        return db.get_job_document_refs(self._conn, job_id)

    def mark_completed(self, job: ClaimedAnalysisJob, result: dict[str, Any]) -> str:
        job_id = uuid.UUID(job.analysis_id)
        return db.save_success(self._conn, job_id, result)

    def mark_failed(self, job: ClaimedAnalysisJob, error_message: str) -> None:
        job_id = uuid.UUID(job.analysis_id)
        db.mark_failed(self._conn, job_id, error_message)

    def mark_needs_review(
        self,
        job: ClaimedAnalysisJob,
        result: dict[str, Any],
        reason: str | None = None,
    ) -> str:
        # Current schema maps human review to VALID_WITH_WARNINGS via save_success.
        return self.mark_completed(job, result)
