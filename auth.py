import json
from pathlib import Path

_COOKIE_FILE = Path(".cookies.json")


def save_cookies(cookies: list[dict]) -> None:
    _COOKIE_FILE.write_text(json.dumps(cookies))


def load_cookies() -> list[dict] | None:
    if _COOKIE_FILE.exists():
        return json.loads(_COOKIE_FILE.read_text())
    return None
