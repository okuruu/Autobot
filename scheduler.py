import time


def run_scheduler(check_fn, interval_hours: int) -> None:
    while True:
        check_fn()
        time.sleep(interval_hours * 3600)
