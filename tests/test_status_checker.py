from unittest.mock import MagicMock, patch
import status_checker
from sites.base import ApplicationStatus

def test_check_statuses_updates_each_application(config, env):
    mock_site = MagicMock()
    mock_site.get_application_statuses.return_value = [
        ApplicationStatus(url="https://example.com/job/1", status="Shortlisted"),
        ApplicationStatus(url="https://example.com/job/2", status="Rejected"),
    ]
    with patch("status_checker.JobStreetSite", return_value=mock_site):
        with patch("status_checker.logger.update_status") as mock_update:
            with patch("status_checker.sync_playwright") as mock_pw:
                mock_pw.return_value.__enter__.return_value.chromium.launch.return_value = MagicMock()
                status_checker.check_statuses(config, env)
    assert mock_update.call_count == 2
    mock_update.assert_any_call(
        url="https://example.com/job/1", new_status="Shortlisted", config=config, env=env
    )
    mock_update.assert_any_call(
        url="https://example.com/job/2", new_status="Rejected", config=config, env=env
    )
