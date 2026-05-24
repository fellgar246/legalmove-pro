import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import db
from pipeline.result_mapper import map_extraction_to_final_report
from tests.fixtures import sample_granular_extraction_output, sample_granular_low_confidence


def test_granular_fixture_maps_to_detected_change_rows():
    report = map_extraction_to_final_report(sample_granular_extraction_output())

    cursor = MagicMock()
    job_id = uuid.uuid4()
    inserted = db.save_detected_changes(cursor, job_id, report["changes"])

    assert inserted == 2
    insert_calls = [
        call
        for call in cursor.execute.call_args_list
        if "INSERT INTO detected_changes" in call.args[0]
    ]
    assert len(insert_calls) == 2

    first_row = insert_calls[0].args[1]
    assert first_row[2] == "MODIFICATION"
    assert first_row[3] == "Payment Terms"
    assert first_row[5] == "Net 30 days."
    assert first_row[6] == "Net 45 days."
    assert first_row[8] == "MEDIUM"
    assert first_row[11] == "HIGH"
    assert first_row[12] is not None
    assert first_row[12].obj["original_quote"] == "Net 30 days."
    assert first_row[12].obj["amendment_quote"] == "Net 45 days."


def test_low_confidence_granular_maps_to_valid_with_warnings():
    report = map_extraction_to_final_report(sample_granular_low_confidence())

    assert report["validation"]["status"] == "VALID_WITH_WARNINGS"
    assert report["changes"][0]["requires_human_review"] is True

    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    job_id = uuid.uuid4()

    status = db.save_success(conn, job_id, report)

    assert status == "VALID_WITH_WARNINGS"
    update_call = cursor.execute.call_args_list[-1]
    assert update_call.args[1][0] == "VALID_WITH_WARNINGS"
