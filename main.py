import argparse
import yaml
from dotenv import dotenv_values
from playwright.sync_api import sync_playwright
from anthropic import Anthropic
import ai_agent
import logger
import status_checker
import scheduler
from sites.jobstreet import JobStreetSite

def _load_config() -> tuple[dict, dict]:
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    env = dotenv_values(".env")
    return config, env

def main() -> None:
    parser = argparse.ArgumentParser(description="Autonomous job application bot")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check-status", action="store_true")
    parser.add_argument("--schedule", action="store_true")
    args = parser.parse_args()

    config, env = _load_config()

    if args.check_status:
        status_checker.check_statuses(config, env)
        return

    if args.schedule:
        scheduler.run_scheduler(
            lambda: status_checker.check_statuses(config, env),
            config["scheduler"]["check_interval_hours"],
        )
        return

    ai_agent.load_cv_cache(config)
    client = Anthropic(api_key=env.get("ANTHROPIC_API_KEY"))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        sites = [JobStreetSite(browser, config, env)]

        for site in sites:
            site.login()
            for keyword in config["jobstreet"]["keywords"]:
                for listing in site.search_jobs([keyword], config["jobstreet"]["location"]):
                    try:
                        job = site.get_job_detail(listing)
                        result = ai_agent.screen(client, job.description, config)
                        cv_display = ai_agent.CV_DISPLAY_NAMES[result["cv_choice"]]

                        if result["match_score"] < config["ai"]["screening_threshold"]:
                            logger.log_application(
                                company=listing.company, title=listing.title,
                                url=listing.url, site_name=listing.site,
                                cv_used=cv_display, match_score=result["match_score"],
                                status="Skipped", cover_letter="", config=config, env=env,
                            )
                            continue

                        letter = ai_agent.cover_letter(
                            client, job.description, result["cv_choice"],
                            listing.company, listing.title, config,
                        )

                        if args.dry_run:
                            print(f"[DRY RUN] {listing.title} @ {listing.company}")
                            status = "Dry Run"
                        else:
                            status = "Applied" if site.apply(job, config["cv"][result["cv_choice"]], letter) else "Failed"

                        logger.log_application(
                            company=listing.company, title=listing.title,
                            url=listing.url, site_name=listing.site,
                            cv_used=cv_display, match_score=result["match_score"],
                            status=status, cover_letter=letter, config=config, env=env,
                        )
                    except Exception as e:
                        print(f"Error on {listing.url}: {e}")
                        logger.log_application(
                            company=listing.company, title=listing.title,
                            url=listing.url, site_name=listing.site,
                            cv_used="", match_score=0, status="Failed",
                            cover_letter=str(e), config=config, env=env,
                        )
        browser.close()

if __name__ == "__main__":
    main()
