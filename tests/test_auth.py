import json
import auth


def test_save_and_load_cookies(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cookies = [{"name": "session", "value": "abc123", "domain": ".jobstreet.com"}]
    auth.save_cookies(cookies)
    assert auth.load_cookies() == cookies


def test_load_cookies_returns_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert auth.load_cookies() is None


def test_save_cookies_overwrites_existing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    auth.save_cookies([{"name": "old", "value": "1"}])
    auth.save_cookies([{"name": "new", "value": "2"}])
    assert auth.load_cookies() == [{"name": "new", "value": "2"}]
