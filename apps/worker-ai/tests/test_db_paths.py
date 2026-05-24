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


def test_get_job_document_paths_resolves_files(db_conn, tmp_path, monkeypatch):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()

    original_file = uploads_dir / "orig.png"
    amendment_file = uploads_dir / "amend.png"
    original_file.write_bytes(b"orig")
    amendment_file.write_bytes(b"amend")

    original_doc_id = uuid.uuid4()
    amendment_doc_id = uuid.uuid4()
    job_id = uuid.uuid4()

    monkeypatch.setenv("UPLOADS_DIR", str(uploads_dir))

    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO documents (
                id, filename, original_filename, mime_type, file_size,
                storage_path, document_role, status
            ) VALUES
                (%s, 'orig.png', 'orig.png', 'image/png', 4, %s, 'ORIGINAL', 'UPLOADED'),
                (%s, 'amend.png', 'amend.png', 'image/png', 5, %s, 'AMENDMENT', 'UPLOADED')
            """,
            (
                original_doc_id,
                str(original_file),
                amendment_doc_id,
                str(amendment_file),
            ),
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
        original_path, amendment_path = db.get_job_document_paths(db_conn, job_id)
        assert original_path == str(original_file.resolve())
        assert amendment_path == str(amendment_file.resolve())
    finally:
        with db_conn.cursor() as cur:
            cur.execute("DELETE FROM analysis_jobs WHERE id = %s", (job_id,))
            cur.execute(
                "DELETE FROM documents WHERE id IN (%s, %s)",
                (original_doc_id, amendment_doc_id),
            )
        db_conn.commit()
