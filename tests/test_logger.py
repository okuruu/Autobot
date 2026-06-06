import csv
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import logger

@pytest.fixture
def mock_sheet():
    sheet = MagicMock()
    sheet.row_values.return_value = ["Date Applied"]  # header already present
    sheet.get_all_records.return_value = [
        {"Job URL": "https://example.com/job/1", "Status": "Applied"}
    ]
    return sheet

def test_log_application_appends_correct_row(config, env, mock_sheet):
    with patch("logger._get_sheet", return_value=mock_sheet):
        logger.log_application(
            company="PT Contoh", title="Head of IT",
            url="https://example.com/job/1", site_name="JobStreet",
            cv_used="Head of IT Developments", match_score=82,
            status="Applied", cover_letter="Dear Hiring Manager...",
            config=config, env=env,
        )
    row = mock_sheet.append_row.call_args[0][0]
    assert row[1] == "PT Contoh"
    assert row[2] == "Head of IT"
    assert row[5] == "Head of IT Developments"
    assert row[6] == 82
    assert row[7] == "Applied"

def test_log_application_falls_back_to_csv(tmp_path, config, env, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("logger._get_sheet", side_effect=Exception("Sheets down")):
        logger.log_application(
            company="PT X", title="Engineer",
            url="https://example.com/2", site_name="JobStreet",
            cv_used="Senior Software Engineer", match_score=60,
            status="Applied", cover_letter="...",
            config=config, env=env,
        )
    rows = list(csv.reader((tmp_path / "fallback.csv").open()))
    assert rows[0][1] == "PT X"

def test_update_status_modifies_correct_cells(config, env, mock_sheet):
    with patch("logger._get_sheet", return_value=mock_sheet):
        logger.update_status("https://example.com/job/1", "Shortlisted", config, env)
    updated_cells = {(c.args[0], c.args[1]) for c in mock_sheet.update_cell.call_args_list}
    assert (2, 8) in updated_cells   # row 2, Status column (index 7 + 1)
    assert (2, 9) in updated_cells   # row 2, Last Checked column (index 8 + 1)

def test_update_status_no_op_for_unknown_url(config, env, mock_sheet):
    with patch("logger._get_sheet", return_value=mock_sheet):
        logger.update_status("https://not-found.com", "Rejected", config, env)
    mock_sheet.update_cell.assert_not_called()
