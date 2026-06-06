import pytest

@pytest.fixture
def config():
    return {
        "cv": {
            "head_of_it": "CV/Head of IT Developments.pdf",
            "senior_engineer": "CV/Senior Software Engineer.pdf",
        },
        "ai": {
            "screening_threshold": 75,
            "screening_model": "claude-haiku-4-5-20251001",
            "cover_letter_model": "claude-sonnet-4-6",
        },
        "jobstreet": {
            "keywords": ["Software Engineer"],
            "location": "Indonesia",
            "salary_min": 0,
        },
        "scheduler": {"check_interval_hours": 12},
    }

@pytest.fixture
def env():
    return {
        "ANTHROPIC_API_KEY": "test-key",
        "GOOGLE_SHEETS_CREDENTIALS": "path/to/creds.json",
        "GOOGLE_SHEET_ID": "test-sheet-id",
        "JOBSTREET_EMAIL": "test@example.com",
        "JOBSTREET_PASSWORD": "testpass",
    }
