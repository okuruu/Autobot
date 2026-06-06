import json
from unittest.mock import MagicMock, PropertyMock, patch
import pytest
from sites.base import JobListing, JobDetail
from sites.jobstreet import JobStreetSite

@pytest.fixture
def browser_page(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    browser = MagicMock()
    page = MagicMock()
    page.context = MagicMock()
    browser.new_page.return_value = page
    return browser, page

def test_login_uses_cookies_when_available(browser_page, config, env, tmp_path):
    browser, page = browser_page
    (tmp_path / ".cookies.json").write_text(json.dumps([{"name": "ses", "value": "x"}]))
    type(page).url = PropertyMock(return_value="https://id.jobstreet.com/en/")
    site = JobStreetSite(browser, config, env)
    with patch("sites.jobstreet.time.sleep"):
        site.login()
    page.context.add_cookies.assert_called_once()
    page.fill.assert_not_called()

def test_login_full_flow_without_cookies(browser_page, config, env):
    browser, page = browser_page
    type(page).url = PropertyMock(return_value="https://id.jobstreet.com/en/")
    page.context.cookies.return_value = []
    site = JobStreetSite(browser, config, env)
    with patch("sites.jobstreet.time.sleep"):
        site.login()
    page.fill.assert_any_call("[name='username']", env["JOBSTREET_EMAIL"])
    page.fill.assert_any_call("[name='password']", env["JOBSTREET_PASSWORD"])

def test_search_jobs_returns_listings(browser_page, config, env):
    browser, page = browser_page
    card = MagicMock()
    card.query_selector.side_effect = lambda sel: {
        "[data-testid='job-title']": MagicMock(inner_text=lambda: "Head of IT"),
        "[data-testid='company-name']": MagicMock(inner_text=lambda: "PT Contoh"),
        "a": MagicMock(get_attribute=lambda _: "https://id.jobstreet.com/en/job/123"),
    }.get(sel)
    page.query_selector_all.return_value = [card]
    site = JobStreetSite(browser, config, env)
    with patch("sites.jobstreet.time.sleep"):
        listings = site.search_jobs(["Head of IT"], "Indonesia")
    assert len(listings) == 1
    assert listings[0].title == "Head of IT"
    assert listings[0].company == "PT Contoh"
    assert listings[0].site == "JobStreet"

def test_apply_returns_true_on_success(browser_page, config, env):
    browser, page = browser_page
    page.query_selector.side_effect = lambda sel: MagicMock()
    type(page).url = PropertyMock(return_value="https://id.jobstreet.com/en/apply/success")
    listing = JobListing(title="Head of IT", company="PT X", url="https://example.com/1", site="JobStreet")
    job = JobDetail(listing=listing, description="desc")
    site = JobStreetSite(browser, config, env)
    with patch("sites.jobstreet.time.sleep"):
        result = site.apply(job, "CV/Head of IT Developments.pdf", "Dear Hiring Manager...")
    assert result is True
