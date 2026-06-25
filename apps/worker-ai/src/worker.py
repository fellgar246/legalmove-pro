import logging
from typing import Any

from config import AWS_REGION, DOCUMENT_TEMP_DIR, S3_BUCKET, WORKER_USE_MOCK_RESULT
from pipeline.contract_analysis import run_contract_analysis
from pipeline.errors import DocumentLoadError, PipelineError
from job_queues.job_queue import ClaimedAnalysisJob, JobQueue
from storage.document_materializer import (
    DocumentMaterializer,
    DocumentStorageRef,
    MaterializedDocument,
)

logger = logging.getLogger(__name__)

_materializer: DocumentMaterializer | None = None

_UNEXPECTED_WORKER_ERROR = (
    "Unexpected worker error. Check worker logs for details."
)


def _build_mock_result() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "disclaimer": "AI-generated review support. Not legal advice.",
        "analysis_summary": {
            "executive_summary": "Mock analysis completed...",
            "overall_risk_level": "MEDIUM",
            "total_changes": 1,
            "high_risk_changes": 0,
            "requires_human_review": True,
        },
        "changes": [
            {
                "change_id": "chg_001",
                "change_type": "MODIFICATION",
                "legal_topic": "Payment Terms",
                "section_reference": "Clause 3",
                "before_text": "Original payment terms placeholder.",
                "after_text": "Modified payment terms placeholder.",
                "summary": "The amendment modifies payment-related obligations.",
                "risk_level": "MEDIUM",
                "requires_human_review": True,
            }
        ],
        "human_review_recommendations": [
            "Review payment terms manually before relying on this report."
        ],
        "validation": {
            "status": "VALID",
            "warnings": [],
        },
    }


def _get_materializer() -> DocumentMaterializer:
    global _materializer
    if _materializer is None:
        _materializer = DocumentMaterializer(
            aws_region=AWS_REGION,
            s3_bucket=S3_BUCKET,
            temp_dir=DOCUMENT_TEMP_DIR,
        )
    return _materializer


def _materialize_job_documents(
    refs: tuple[DocumentStorageRef, DocumentStorageRef],
) -> tuple[list[MaterializedDocument], str, str]:
    materializer = _get_materializer()
    materialized: list[MaterializedDocument] = []

    try:
        original = materializer.materialize(refs[0])
        materialized.append(original)
        amendment = materializer.materialize(refs[1])
        materialized.append(amendment)
    except Exception:
        for item in materialized:
            materializer.cleanup(item)
        raise

    return materialized, original.local_path, amendment.local_path


def _cleanup_materialized_documents(materialized: list[MaterializedDocument]) -> None:
    materializer = _get_materializer()
    for item in materialized:
        materializer.cleanup(item)


def _format_validation_failure(result: dict[str, Any]) -> str:
    validation = result.get("validation") or {}
    warnings = validation.get("warnings") or []
    if warnings:
        return "Validation failed: " + "; ".join(warnings)
    return "Validation failed: report validation status is INVALID."


def process_job(job_queue: JobQueue, job: ClaimedAnalysisJob) -> None:
    job_id = job.analysis_id
    print(f"[worker] processing job {job_id}")
    materialized_docs: list[MaterializedDocument] = []
    try:
        refs = job_queue.get_job_document_refs(job)
        materialized_docs, original_path, amendment_path = _materialize_job_documents(refs)
        print(
            f"[worker] materialized document paths for job {job_id}: "
            f"original={original_path}, amendment={amendment_path}"
        )

        if WORKER_USE_MOCK_RESULT:
            print(f"[worker] mock mode enabled for job {job_id}")
            result = _build_mock_result()
        else:
            result = run_contract_analysis(
                analysis_job_id=job_id,
                original_file_path=original_path,
                amendment_file_path=amendment_path,
            )
            print(f"[worker] pipeline completed for job {job_id}")

        validation_status = (result.get("validation") or {}).get("status")
        if validation_status == "INVALID":
            error_message = _format_validation_failure(result)
            print(f"[worker] failed job {job_id}: {error_message}")
            job_queue.mark_failed(job, error_message)
            return

        changes_count = len(result.get("changes") or [])
        if validation_status == "VALID_WITH_WARNINGS":
            job_status = job_queue.mark_needs_review(job, result)
        else:
            job_status = job_queue.mark_completed(job, result)
        if changes_count == 0:
            print(f"[worker] job {job_id} saved with 0 detected changes")
        else:
            print(f"[worker] job {job_id} saved with {changes_count} detected changes")
        print(f"[worker] completed job {job_id} with status {job_status}")
    except PipelineError as exc:
        error_message = str(exc)
        logger.exception("[worker] pipeline failed job %s", job_id)
        print(f"[worker] failed job {job_id}: {error_message}")
        job_queue.mark_failed(job, error_message)
    except FileNotFoundError as exc:
        error_message = str(DocumentLoadError(str(exc)))
        logger.exception("[worker] document not found job %s", job_id)
        print(f"[worker] failed job {job_id}: {error_message}")
        job_queue.mark_failed(job, error_message)
    except Exception:
        logger.exception("[worker] unexpected error job %s", job_id)
        print(f"[worker] failed job {job_id}: {_UNEXPECTED_WORKER_ERROR}")
        job_queue.mark_failed(job, _UNEXPECTED_WORKER_ERROR)
    finally:
        _cleanup_materialized_documents(materialized_docs)


def run_once(job_queue: JobQueue) -> None:
    job = job_queue.claim_next_job()
    if job is None:
        print("[worker] no queued jobs")
        return
    print(f"[worker] claimed job {job.analysis_id}")
    process_job(job_queue, job)
