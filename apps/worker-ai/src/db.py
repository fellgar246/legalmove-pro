import uuid
from typing import Any

import psycopg
from psycopg import Connection
from psycopg.types.json import Json

from storage.document_materializer import DocumentStorageRef


def get_connection(database_url: str) -> Connection:
    return psycopg.connect(database_url, autocommit=False)


def _build_document_ref(
    document_id: uuid.UUID,
    storage_provider: str | None,
    storage_path: str,
    storage_key: str | None,
    original_filename: str | None,
    mime_type: str | None,
) -> DocumentStorageRef:
    return DocumentStorageRef(
        document_id=str(document_id),
        storage_provider=storage_provider or "local",
        storage_path=storage_path,
        storage_key=storage_key,
        original_filename=original_filename,
        content_type=mime_type,
    )


def get_job_document_refs(
    conn: Connection, job_id: uuid.UUID
) -> tuple[DocumentStorageRef, DocumentStorageRef]:
    query = """
        SELECT
            d_orig.id, d_orig.storage_provider, d_orig.storage_path,
            d_orig.storage_key, d_orig.original_filename, d_orig.mime_type,
            d_amend.id, d_amend.storage_provider, d_amend.storage_path,
            d_amend.storage_key, d_amend.original_filename, d_amend.mime_type
        FROM analysis_jobs j
        JOIN documents d_orig ON d_orig.id = j.original_document_id
        JOIN documents d_amend ON d_amend.id = j.amendment_document_id
        WHERE j.id = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (job_id,))
        row = cur.fetchone()

    if row is None:
        raise ValueError(f"Analysis job not found: {job_id}")

    return (
        _build_document_ref(*row[0:6]),
        _build_document_ref(*row[6:12]),
    )


TERMINAL_JOB_STATUSES = frozenset({"COMPLETED", "FAILED", "VALID_WITH_WARNINGS"})


def get_job_status(conn: Connection, job_id: uuid.UUID) -> str | None:
    query = """
        SELECT status
        FROM analysis_jobs
        WHERE id = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (job_id,))
        row = cur.fetchone()

    if row is None:
        return None
    return row[0]


def claim_analysis_job_by_id(conn: Connection, job_id: uuid.UUID) -> bool:
    query = """
        UPDATE analysis_jobs
        SET status = 'PROCESSING', started_at = NOW(), updated_at = NOW()
        WHERE id = %s AND status = 'QUEUED'
        RETURNING id
    """
    with conn.cursor() as cur:
        cur.execute(query, (job_id,))
        row = cur.fetchone()
    conn.commit()
    return row is not None


def claim_next_job(conn: Connection) -> uuid.UUID | None:
    query = """
        UPDATE analysis_jobs
        SET status = 'PROCESSING', started_at = NOW(), updated_at = NOW()
        WHERE id = (
            SELECT id FROM analysis_jobs
            WHERE status = 'QUEUED'
            ORDER BY created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id
    """
    with conn.cursor() as cur:
        cur.execute(query)
        row = cur.fetchone()
    conn.commit()

    if row is None:
        return None
    return row[0]


def _resolve_job_status(validation_status: str) -> str:
    if validation_status == "VALID_WITH_WARNINGS":
        return "VALID_WITH_WARNINGS"
    return "COMPLETED"


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def _optional_evidence(value: Any) -> Json | None:
    if not isinstance(value, dict) or not value:
        return None
    return Json(value)


def _normalize_change_row(
    analysis_job_id: uuid.UUID, change: dict[str, Any]
) -> tuple[Any, ...]:
    """Map FinalAnalysisReport v1 change item to detected_changes INSERT tuple."""
    return (
        uuid.uuid4(),
        analysis_job_id,
        change.get("change_type") or "MODIFICATION",
        change.get("legal_topic"),
        change.get("section_reference"),
        change.get("before_text"),
        change.get("after_text"),
        change.get("summary") or "No summary provided.",
        change.get("risk_level") or "MEDIUM",
        change.get("requires_human_review", True),
        _optional_text(change.get("impact_explanation")),
        _optional_text(change.get("confidence")),
        _optional_evidence(change.get("evidence")),
    )


def save_detected_changes(
    cur: psycopg.Cursor,
    analysis_job_id: uuid.UUID,
    changes: list[dict[str, Any]],
) -> int:
    """
    Replace detected_changes for a job and insert normalized rows.
    Returns the number of rows inserted (0 if changes is empty).
    """
    delete_changes = """
        DELETE FROM detected_changes
        WHERE analysis_job_id = %s
    """
    insert_change = """
        INSERT INTO detected_changes (
            id, analysis_job_id, change_type, legal_topic, section_reference,
            before_text, after_text, summary, risk_level, requires_human_review,
            impact_explanation, confidence, evidence
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cur.execute(delete_changes, (analysis_job_id,))

    if not changes:
        return 0

    for change in changes:
        cur.execute(insert_change, _normalize_change_row(analysis_job_id, change))

    return len(changes)


def save_success(conn: Connection, job_id: uuid.UUID, result: dict[str, Any]) -> str:
    result_id = uuid.uuid4()
    schema_version = result["schema_version"]
    validation_status = result["validation"]["status"]
    job_status = _resolve_job_status(validation_status)
    changes = result.get("changes") or []

    insert_result = """
        INSERT INTO analysis_results (id, analysis_job_id, result_json, schema_version, validation_status)
        VALUES (%s, %s, %s, %s, %s)
    """
    update_job = """
        UPDATE analysis_jobs
        SET status = %s, completed_at = NOW(), updated_at = NOW()
        WHERE id = %s
    """

    try:
        with conn.cursor() as cur:
            cur.execute(
                insert_result,
                (result_id, job_id, Json(result), schema_version, validation_status),
            )
            save_detected_changes(cur, job_id, changes)
            cur.execute(update_job, (job_status, job_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return job_status


def mark_failed(conn: Connection, job_id: uuid.UUID, error_message: str) -> None:
    query = """
        UPDATE analysis_jobs
        SET status = 'FAILED', error_message = %s, completed_at = NOW(), updated_at = NOW()
        WHERE id = %s
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query, (error_message, job_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
