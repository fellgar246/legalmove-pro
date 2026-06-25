"""Job queue abstraction for analysis job lifecycle."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from storage.document_materializer import DocumentStorageRef


@dataclass(frozen=True)
class ClaimedAnalysisJob:
    analysis_id: str
    original_document_id: str | None = None
    amendment_document_id: str | None = None
    status: str = "PROCESSING"
    metadata: dict[str, Any] | None = field(default=None)


class JobQueue(ABC):
    """Abstract job source for claiming and updating analysis jobs."""

    @abstractmethod
    def claim_next_job(self) -> ClaimedAnalysisJob | None:
        """Claim the next pending job, or return None if the queue is empty."""

    @abstractmethod
    def get_job_document_refs(
        self, job: ClaimedAnalysisJob
    ) -> tuple[DocumentStorageRef, DocumentStorageRef]:
        """Load document storage references for the claimed job."""

    @abstractmethod
    def mark_completed(self, job: ClaimedAnalysisJob, result: dict[str, Any]) -> str:
        """Persist a successful result and return the final job status."""

    @abstractmethod
    def mark_failed(self, job: ClaimedAnalysisJob, error_message: str) -> None:
        """Mark the job as failed with a user-facing error message."""

    @abstractmethod
    def mark_needs_review(
        self,
        job: ClaimedAnalysisJob,
        result: dict[str, Any],
        reason: str | None = None,
    ) -> str:
        """Persist a result that requires human review and return job status."""
