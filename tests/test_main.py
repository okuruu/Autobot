from unittest.mock import MagicMock, patch
import pytest
import main
from sites.base import JobListing, JobDetail

def test_check_status_flag_routes_to_checker(config, env):
    mock_check = MagicMock()
    with patch("sys.argv", ["main.py", "--check-status"]):
        with patch("main._load_config", return_value=(config, env)):
            with patch("main.status_checker.check_statuses", mock_check):
                main.main()
    mock_check.assert_called_once_with(config, env)

def test_schedule_flag_routes_to_scheduler(config, env):
    mock_sched = MagicMock()
    with patch("sys.argv", ["main.py", "--schedule"]):
        with patch("main._load_config", return_value=(config, env)):
            with patch("main.scheduler.run_scheduler", mock_sched):
                main.main()
    mock_sched.assert_called_once()

def test_dry_run_logs_dry_run_status(config, env):
    listing = JobListing(title="Head of IT", company="PT X", url="https://example.com/1", site="JobStreet")
    job = JobDetail(listing=listing, description="desc")
    mock_site = MagicMock()
    mock_site.search_jobs.return_value = [listing]
    mock_site.get_job_detail.return_value = job
    mock_log = MagicMock()

    with patch("sys.argv", ["main.py", "--dry-run"]):
        with patch("main._load_config", return_value=(config, env)):
            with patch("main.JobStreetSite", return_value=mock_site):
                with patch("main.ai_agent.load_cv_cache"):
                    with patch("main.ai_agent.screen", return_value={"match_score": 85, "cv_choice": "head_of_it", "reason": "x"}):
                        with patch("main.ai_agent.cover_letter", return_value="Dear HM..."):
                            with patch("main.logger.log_application", mock_log):
                                with patch("main.Anthropic"):
                                    with patch("main.sync_playwright") as pw:
                                        pw.return_value.__enter__.return_value.chromium.launch.return_value = MagicMock()
                                        main.main()

    mock_log.assert_called_once()
    kwargs = mock_log.call_args.kwargs
    assert kwargs["status"] == "Dry Run"
    assert kwargs["company"] == "PT X"
