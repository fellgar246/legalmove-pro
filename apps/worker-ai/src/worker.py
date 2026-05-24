import logging
import uuid
from typing import Any

from psycopg import Connection

import db
from config import WORKER_USE_MOCK_RESULT
from pipeline.contract_analysis import run_contract_analysis
from pipeline.errors import DocumentLoadError, PipelineError

logger = logging.getLogger(__name__)

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


def _format_validation_failure(result: dict[str, Any]) -> str:
    validation = result.get("validation") or {}
    warnings = validation.get("warnings") or []
    if warnings:
        return "Validation failed: " + "; ".join(warnings)
    return "Validation failed: report validation status is INVALID."


def process_job(conn: Connection, job_id: uuid.UUID) -> None:
    print(f"[worker] processing job {job_id}")
    try:
        original_path, amendment_path = db.get_job_document_paths(conn, job_id)
        print(
            f"[worker] resolved document paths for job {job_id}: "
            f"original={original_path}, amendment={amendment_path}"
        )

        if WORKER_USE_MOCK_RESULT:
            print(f"[worker] mock mode enabled for job {job_id}")
            result = _build_mock_result()
        else:
            result = run_contract_analysis(
                analysis_job_id=str(job_id),
                original_file_path=original_path,
                amendment_file_path=amendment_path,
            )
            print(f"[worker] pipeline completed for job {job_id}")

        validation_status = (result.get("validation") or {}).get("status")
        if validation_status == "INVALID":
            error_message = _format_validation_failure(result)
            print(f"[worker] failed job {job_id}: {error_message}")
            db.mark_failed(conn, job_id, error_message)
            return

        changes_count = len(result.get("changes") or [])
        job_status = db.save_success(conn, job_id, result)
        if changes_count == 0:
            print(f"[worker] job {job_id} saved with 0 detected changes")
        else:
            print(f"[worker] job {job_id} saved with {changes_count} detected changes")
        print(f"[worker] completed job {job_id} with status {job_status}")
    except PipelineError as exc:
        error_message = str(exc)
        logger.exception("[worker] pipeline failed job %s", job_id)
        print(f"[worker] failed job {job_id}: {error_message}")
        db.mark_failed(conn, job_id, error_message)
    except FileNotFoundError as exc:
        error_message = str(DocumentLoadError(str(exc)))
        logger.exception("[worker] document not found job %s", job_id)
        print(f"[worker] failed job {job_id}: {error_message}")
        db.mark_failed(conn, job_id, error_message)
    except Exception:
        logger.exception("[worker] unexpected error job %s", job_id)
        print(f"[worker] failed job {job_id}: {_UNEXPECTED_WORKER_ERROR}")
        db.mark_failed(conn, job_id, _UNEXPECTED_WORKER_ERROR)


def run_once(conn: Connection) -> None:
    job_id = db.claim_next_job(conn)
    if job_id is None:
        print("[worker] no queued jobs")
        return
    print(f"[worker] claimed job {job_id}")
    process_job(conn, job_id)
