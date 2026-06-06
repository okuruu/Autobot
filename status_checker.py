from playwright.sync_api import sync_playwright
from sites.jobstreet import JobStreetSite
import logger

def check_statuses(config: dict, env: dict) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        try:
            site = JobStreetSite(browser, config, env)
            site.login()
            for s in site.get_application_statuses():
                logger.update_status(url=s.url, new_status=s.status, config=config, env=env)
        finally:
            browser.close()
