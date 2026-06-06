import random
import time
from playwright.sync_api import Browser
from auth import save_cookies, load_cookies
from sites.base import BaseSite, JobListing, JobDetail, ApplicationStatus

class JobStreetSite(BaseSite):
    BASE_URL = "https://id.jobstreet.com"

    def __init__(self, browser: Browser, config: dict, env: dict) -> None:
        self.config = config
        self.env = env
        self.page = browser.new_page()

    def _pause(self) -> None:
        time.sleep(random.uniform(2, 5))

    def _is_logged_in(self) -> bool:
        return "login" not in self.page.url and "oauth" not in self.page.url

    def login(self) -> None:
        cookies = load_cookies()
        if cookies:
            self.page.context.add_cookies(cookies)
            self.page.goto(f"{self.BASE_URL}/en/")
            self._pause()
            if self._is_logged_in():
                return
        self.page.goto(f"{self.BASE_URL}/oauth/login")
        self._pause()
        self.page.fill("[name='username']", self.env["JOBSTREET_EMAIL"])
        self.page.click("[data-testid='login-btn']")
        self._pause()
        self.page.fill("[name='password']", self.env["JOBSTREET_PASSWORD"])
        self.page.click("[data-testid='login-submit']")
        self.page.wait_for_load_state("networkidle")
        save_cookies(self.page.context.cookies())

    def search_jobs(self, keywords: list[str], location: str) -> list[JobListing]:
        results: list[JobListing] = []
        for keyword in keywords:
            self.page.goto(f"{self.BASE_URL}/en/jobs")
            self._pause()
            self.page.fill("[data-testid='keywords-input']", keyword)
            self.page.fill("[data-testid='location-input']", location)
            self.page.press("[data-testid='location-input']", "Enter")
            self.page.wait_for_load_state("networkidle")
            self._pause()
            for card in self.page.query_selector_all("[data-testid='job-card']"):
                title_el = card.query_selector("[data-testid='job-title']")
                company_el = card.query_selector("[data-testid='company-name']")
                link_el = card.query_selector("a")
                if title_el and company_el and link_el:
                    results.append(JobListing(
                        title=title_el.inner_text().strip(),
                        company=company_el.inner_text().strip(),
                        url=link_el.get_attribute("href"),
                        site="JobStreet",
                    ))
        return results

    def get_job_detail(self, listing: JobListing) -> JobDetail:
        self.page.goto(listing.url)
        self.page.wait_for_load_state("networkidle")
        self._pause()
        desc_el = self.page.query_selector("[data-testid='job-details-body']")
        return JobDetail(listing=listing, description=desc_el.inner_text() if desc_el else "")

    def apply(self, job: JobDetail, cv_path: str, cover_letter: str) -> bool:
        self.page.goto(job.listing.url)
        self._pause()
        apply_btn = self.page.query_selector("[data-testid='apply-button']")
        if not apply_btn:
            return False
        apply_btn.click()
        self._pause()
        file_input = self.page.query_selector("input[type='file']")
        if file_input:
            file_input.set_input_files(cv_path)
        cover_area = self.page.query_selector(
            "textarea[name='coverLetter'], textarea[placeholder*='cover']"
        )
        if cover_area:
            cover_area.fill(cover_letter)
        self._pause()
        submit = self.page.query_selector(
            "[data-testid='submit-application'], button[type='submit']"
        )
        if not submit:
            return False
        submit.click()
        self.page.wait_for_load_state("networkidle")
        return (
            "success" in self.page.url
            or self.page.query_selector("[data-testid='application-success']") is not None
        )

    def get_application_statuses(self) -> list[ApplicationStatus]:
        self.page.goto(f"{self.BASE_URL}/en/my-activity/applications")
        self.page.wait_for_load_state("networkidle")
        self._pause()
        statuses: list[ApplicationStatus] = []
        for row in self.page.query_selector_all("[data-testid='application-card']"):
            link_el = row.query_selector("a[href*='/job/']")
            status_el = row.query_selector("[data-testid='application-status']")
            if link_el and status_el:
                statuses.append(ApplicationStatus(
                    url=link_el.get_attribute("href"),
                    status=status_el.inner_text().strip(),
                ))
        return statuses
