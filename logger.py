import csv
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

COLUMNS = [
    "Date Applied", "Company", "Job Title", "Job URL", "Site",
    "CV Used", "Match Score", "Status", "Last Checked", "Cover Letter",
]

def _get_sheet(config: dict, env: dict):
    creds = Credentials.from_service_account_file(env["GOOGLE_SHEETS_CREDENTIALS"], scopes=_SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(env["GOOGLE_SHEET_ID"]).sheet1
    if not sheet.row_values(1):
        sheet.append_row(COLUMNS)
    return sheet

def log_application(
    company: str, title: str, url: str, site_name: str,
    cv_used: str, match_score: int, status: str, cover_letter: str,
    config: dict, env: dict,
) -> None:
    row = [
        date.today().isoformat(), company, title, url, site_name,
        cv_used, match_score, status, date.today().isoformat(), cover_letter,
    ]
    try:
        _get_sheet(config, env).append_row(row)
    except Exception as e:
        print(f"Warning: Sheets write failed ({e}). Writing to fallback.csv")
        with open("fallback.csv", "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)

def update_status(url: str, new_status: str, config: dict, env: dict) -> None:
    try:
        sheet = _get_sheet(config, env)
        for i, row in enumerate(sheet.get_all_records(), start=2):
            if row.get("Job URL") == url:
                sheet.update_cell(i, COLUMNS.index("Status") + 1, new_status)
                sheet.update_cell(i, COLUMNS.index("Last Checked") + 1, date.today().isoformat())
                return
    except Exception as e:
        print(f"Warning: Status update failed for {url}: {e}")
