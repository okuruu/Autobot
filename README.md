# Autobot — Autonomous Job Application Bot

Autobot searches JobStreet Indonesia for matching jobs, uses Claude AI to screen listings and write tailored cover letters, submits applications automatically, and logs every outcome to Google Sheets. A separate status-checker module periodically syncs application outcomes (Rejected, Shortlisted, etc.) back to the spreadsheet.

---

## Features

- **Job search** — searches JobStreet Indonesia by configurable keywords and location
- **AI screening** — Claude Haiku scores each job 0–100 and picks the best-fit CV version
- **Cover letter generation** — Claude Sonnet writes a unique, tailored cover letter per job
- **CV auto-selection** — automatically chooses between "Head of IT Developments" and "Senior Software Engineer" CVs per role; logs which was used so you can prepare accordingly for interviews
- **Google Sheets logging** — every job (applied, skipped, failed) gets a row with date, company, title, URL, CV used, match score, status, and the full cover letter
- **Status tracking** — revisits the "My Applications" dashboard and syncs current statuses (In Review, Shortlisted, Rejected, Interview) back to the sheet
- **Dry-run mode** — screens and generates cover letters without submitting anything
- **Cookie session persistence** — saves login cookies so re-runs skip the login form
- **Extensible** — adding Glints or Indeed means creating one new file under `sites/` that implements `BaseSite`

---

## Project Structure

```
Autobot/
├── .env.example              # secrets template — copy to .env and fill in
├── config.yaml               # keywords, models, thresholds, schedule interval
├── requirements.txt
├── main.py                   # CLI entry point
│
├── CV/                       # place your CV PDFs here (not committed)
│   ├── Head of IT Developments.pdf
│   └── Senior Software Engineer.pdf
│
├── sites/
│   ├── base.py               # BaseSite interface + shared dataclasses
│   ├── jobstreet.py          # JobStreet implementation
│   ├── glints.py             # (future)
│   └── indeed.py             # (future)
│
├── ai_agent.py               # Claude screening + cover letter + CV cache
├── auth.py                   # browser cookie persistence
├── logger.py                 # Google Sheets writer + CSV fallback
├── status_checker.py         # reads "My Applications", syncs Sheets
├── scheduler.py              # time-based loop for status checker
│
└── tests/                    # 21 unit tests (all passing)
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/okuruu/Autobot.git
cd Autobot
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Place CV files

Drop both PDFs into the `CV/` directory:

```
CV/Head of IT Developments.pdf
CV/Senior Software Engineer.pdf
```

### 3. Configure secrets

```bash
cp .env.example .env
```

Edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_SHEETS_CREDENTIALS=path/to/service-account.json
GOOGLE_SHEET_ID=your-sheet-id-from-the-url
JOBSTREET_EMAIL=your@email.com
JOBSTREET_PASSWORD=yourpassword
```

**Google Sheets setup:**
1. Create a Google Cloud project and enable the Sheets API
2. Create a service account, download the JSON key
3. Create a Google Sheet and share it (Editor access) with the service account email
4. Copy the Sheet ID from the URL (`https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`)

### 4. Adjust config

Edit `config.yaml` to set your search keywords, screening threshold, and schedule interval:

```yaml
jobstreet:
  keywords:
    - "Software Engineer"
    - "Head of IT"
    - "IT Manager"
    - "IT Development"
  location: "Indonesia"

ai:
  screening_threshold: 75    # jobs scoring below this are logged as Skipped
```

---

## Usage

```bash
# Screen jobs and generate cover letters, but don't submit anything
python main.py --dry-run

# Run the full bot — search, screen, apply, log
python main.py

# One-off sync of application statuses to Google Sheets
python main.py --check-status

# Run the status checker on a loop (every 12 hours by default)
python main.py --schedule
```

---

## Google Sheets Schema

The bot writes one row per job:

| Column | Description |
|--------|-------------|
| Date Applied | ISO date of application |
| Company | Company name |
| Job Title | Role title as listed |
| Job URL | Direct link to the listing |
| Site | JobStreet / Glints / etc. |
| CV Used | Which CV was sent — use this to prepare for interviews |
| Match Score | Claude's 0–100 relevance score |
| Status | Applied / Skipped / Failed / In Review / Shortlisted / Rejected / Interview |
| Last Checked | Date the status was last read from the site |
| Cover Letter | Full text of the generated cover letter |

---

## AI & Caching

Two Claude models are used per matched job:

- **claude-haiku-4-5** — fast, cheap screening call. Returns a match score, CV choice, and one-sentence reason.
- **claude-sonnet-4-6** — higher-quality cover letter generation.

**CV prompt caching:** Both CVs are parsed from PDF once at startup and stored in memory. They are sent to Claude with `cache_control: ephemeral` so Claude caches the tokenized content server-side — subsequent jobs re-use the cache at ~10% of normal input token cost instead of re-tokenizing the CV text on every call.

---

## Pending: Task 10 — Selector Verification

> **This step requires real credentials and CV files and must be done before live use.**

The Playwright selectors in `sites/jobstreet.py` are best-effort guesses based on common `data-testid` patterns. They need to be verified against the live JobStreet DOM before the bot can apply to real jobs.

**How to verify:**

```bash
python main.py --dry-run
```

Watch the Chromium browser window that opens. Open DevTools (`F12`) on any page where a step stalls or fails, hover over elements in the Inspector to find the correct selectors, and update `sites/jobstreet.py` accordingly.

**Selectors to check:**

| Method | Selectors |
|--------|-----------|
| `login()` | `[data-testid='login-btn']`, `[data-testid='login-submit']`, `[name='username']`, `[name='password']` |
| `search_jobs()` | `[data-testid='keywords-input']`, `[data-testid='location-input']`, `[data-testid='job-card']`, `[data-testid='job-title']`, `[data-testid='company-name']` |
| `get_job_detail()` | `[data-testid='job-details-body']` |
| `apply()` | `[data-testid='apply-button']`, `input[type='file']`, `textarea[name='coverLetter']`, `[data-testid='submit-application']` |
| `get_application_statuses()` | `[data-testid='application-card']`, `[data-testid='application-status']` |

After verifying and fixing selectors, commit the changes:

```bash
git add sites/jobstreet.py
git commit -m "fix: JobStreet selectors verified against live site"
```

---

## Running Tests

```bash
source venv/bin/activate
venv/bin/pytest tests/ -v
```

All 21 tests should pass. Tests use mocked Playwright pages and a mocked Anthropic client — no real browser or API calls are made.

---

## Adding a New Job Site

1. Create `sites/glints.py` implementing all five methods of `BaseSite` (`login`, `search_jobs`, `get_job_detail`, `apply`, `get_application_statuses`)
2. In `main.py`, add the new site to the `sites` list alongside `JobStreetSite`

`main.py` and `logger.py` never import site-specific code directly — they only talk to the `BaseSite` interface.
