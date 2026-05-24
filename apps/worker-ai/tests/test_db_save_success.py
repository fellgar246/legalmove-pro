import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import db


def test_save_success_sets_completed_for_valid_status():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    job_id = uuid.uuid4()
    result = {
        "schema_version": "1.0",
        "validation": {"status": "VALID"},
        "changes": [],
    }

    status = db.save_success(conn, job_id, result)

    assert status == "COMPLETED"
    update_call = cursor.execute.call_args_list[-1]
    assert update_call.args[1][0] == "COMPLETED"
    conn.commit.assert_called_once()


def test_save_success_sets_valid_with_warnings_status():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    job_id = uuid.uuid4()
    result = {
        "schema_version": "1.0",
        "validation": {"status": "VALID_WITH_WARNINGS"},
        "changes": [],
    }

    status = db.save_success(conn, job_id, result)

    assert status == "VALID_WITH_WARNINGS"
    update_call = cursor.execute.call_args_list[-1]
    assert update_call.args[1][0] == "VALID_WITH_WARNINGS"


def test_save_success_inserts_detected_changes_when_present():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    job_id = uuid.uuid4()
    result = {
        "schema_version": "1.0",
        "validation": {"status": "VALID"},
        "changes": [
            {
                "change_type": "MODIFICATION",
                "legal_topic": "Payment Terms",
                "section_reference": "Clause 3",
                "before_text": "before",
                "after_text": "after",
                "summary": "Changed payment terms.",
                "risk_level": "MEDIUM",
                "requires_human_review": True,
            }
        ],
    }

    db.save_success(conn, job_id, result)

    assert cursor.execute.call_count == 4


def test_save_detected_changes_empty_list():
    cursor = MagicMock()
    job_id = uuid.uuid4()

    inserted = db.save_detected_changes(cursor, job_id, [])

    assert inserted == 0
    cursor.execute.assert_called_once()
    assert "DELETE FROM detected_changes" in cursor.execute.call_args.args[0]


def test_save_detected_changes_applies_defaults():
    cursor = MagicMock()
    job_id = uuid.uuid4()

    inserted = db.save_detected_changes(cursor, job_id, [{}])

    assert inserted == 1
    insert_call = cursor.execute.call_args_list[-1]
    row = insert_call.args[1]
    assert row[2] == "MODIFICATION"
    assert row[7] == "No summary provided."
    assert row[8] == "MEDIUM"
    assert row[9] is True
    assert row[10] is None
    assert row[11] is None
    assert row[12] is None


def test_save_detected_changes_persists_granular_extension_fields():
    cursor = MagicMock()
    job_id = uuid.uuid4()

    inserted = db.save_detected_changes(
        cursor,
        job_id,
        [
            {
                "change_type": "MODIFICATION",
                "legal_topic": "Payment Terms",
                "section_reference": "Clause 3",
                "before_text": "Net 30 days.",
                "after_text": "Net 45 days.",
                "summary": "Payment terms extended.",
                "risk_level": "MEDIUM",
                "requires_human_review": False,
                "impact_explanation": "Cash flow timing may shift.",
                "confidence": "HIGH",
                "evidence": {
                    "original_quote": "Net 30 days.",
                    "amendment_quote": "Net 45 days.",
                },
            }
        ],
    )

    assert inserted == 1
    insert_call = cursor.execute.call_args_list[-1]
    row = insert_call.args[1]
    assert row[10] == "Cash flow timing may shift."
    assert row[11] == "HIGH"
    assert row[12] is not None
    assert row[12].obj["original_quote"] == "Net 30 days."


def test_save_detected_changes_deletes_before_insert():
    cursor = MagicMock()
    job_id = uuid.uuid4()

    db.save_detected_changes(
        cursor,
        job_id,
        [{"summary": "Changed payment terms.", "risk_level": "HIGH"}],
    )

    delete_call = cursor.execute.call_args_list[0]
    insert_call = cursor.execute.call_args_list[1]
    assert "DELETE FROM detected_changes" in delete_call.args[0]
    assert delete_call.args[1] == (job_id,)
    assert "INSERT INTO detected_changes" in insert_call.args[0]


def test_save_success_rollback_on_detected_changes_failure():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    job_id = uuid.uuid4()
    result = {
        "schema_version": "1.0",
        "validation": {"status": "VALID"},
        "changes": [{"summary": "Changed payment terms.", "risk_level": "MEDIUM"}],
    }

    cursor.execute.side_effect = [None, None, RuntimeError("insert failed")]

    with pytest.raises(RuntimeError, match="insert failed"):
        db.save_success(conn, job_id, result)

    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()
