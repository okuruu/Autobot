from unittest.mock import patch
import scheduler


def test_run_scheduler_calls_fn_then_sleeps():
    call_count = {"n": 0}

    def fake_fn():
        call_count["n"] += 1
        if call_count["n"] >= 2:
            raise StopIteration

    with patch("scheduler.time.sleep") as mock_sleep:
        try:
            scheduler.run_scheduler(fake_fn, interval_hours=12)
        except StopIteration:
            pass

    assert call_count["n"] == 2
    mock_sleep.assert_called_with(43200)
