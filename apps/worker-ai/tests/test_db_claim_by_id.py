import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import db
from db import get_connection


@pytest.fixture
def db_conn():
    database_url = "postgres://legalmove:legalmove@localhost:5432/legalmove?sslmode=disable"
    try:
        conn = get_connection(database_url)
    except Exception as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc}")
    yield conn
    conn.close()


def test_claim_analysis_job_by_id_only_claims_queued_job(db_conn):
    job_id = uuid.uuid4()
    original_doc_id = uuid.uuid4()
    amendment_doc_id = uuid.uuid4()

    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO documents (
                id, filename, original_filename, mime_type, file_size,
                storage_path, document_role, status
            ) VALUES
                (%s, 'orig.png', 'orig.png', 'image/png', 4, '/tmp/orig.png', 'ORIGINAL', 'UPLOADED'),
                (%s, 'amend.png', 'amend.png', 'image/png', 5, '/tmp/amend.png', 'AMENDMENT', 'UPLOADED')
            """,
            (original_doc_id, amendment_doc_id),
        )
        cur.execute(
            """
            INSERT INTO analysis_jobs (
                id, original_document_id, amendment_document_id, status
            ) VALUES (%s, %s, %s, 'QUEUED')
            """,
            (job_id, original_doc_id, amendment_doc_id),
        )
    db_conn.commit()

    try:
        assert db.get_job_status(db_conn, job_id) == "QUEUED"
        assert db.claim_analysis_job_by_id(db_conn, job_id) is True
        assert db.get_job_status(db_conn, job_id) == "PROCESSING"
        assert db.claim_analysis_job_by_id(db_conn, job_id) is False
    finally:
        with db_conn.cursor() as cur:
            cur.execute("DELETE FROM analysis_jobs WHERE id = %s", (job_id,))
            cur.execute(
                "DELETE FROM documents WHERE id IN (%s, %s)",
                (original_doc_id, amendment_doc_id),
            )
        db_conn.commit()
