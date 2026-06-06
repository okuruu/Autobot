import json
from unittest.mock import MagicMock, patch
import pytest
import ai_agent

@pytest.fixture(autouse=True)
def reset_cache():
    ai_agent.cv_cache.clear()
    yield
    ai_agent.cv_cache.clear()

def test_load_cv_cache_populates_both_keys(config):
    mock_reader = MagicMock()
    mock_reader.pages = [MagicMock()]
    mock_reader.pages[0].extract_text.return_value = "CV content"
    with patch("ai_agent.PdfReader", return_value=mock_reader):
        ai_agent.load_cv_cache(config)
    assert ai_agent.cv_cache["head_of_it"] == "CV content"
    assert ai_agent.cv_cache["senior_engineer"] == "CV content"

def test_screen_returns_parsed_json(config):
    ai_agent.cv_cache["head_of_it"] = "Head CV"
    ai_agent.cv_cache["senior_engineer"] = "Senior CV"
    payload = {"match_score": 82, "cv_choice": "head_of_it", "reason": "Leadership"}
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=json.dumps(payload))]
    client = MagicMock()
    client.messages.create.return_value = mock_resp
    result = ai_agent.screen(client, "job desc", config)
    assert result == payload

def test_screen_puts_cvs_first_with_cache_control(config):
    ai_agent.cv_cache["head_of_it"] = "Head CV"
    ai_agent.cv_cache["senior_engineer"] = "Senior CV"
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=json.dumps({"match_score": 50, "cv_choice": "senior_engineer", "reason": "x"}))]
    client = MagicMock()
    client.messages.create.return_value = mock_resp
    ai_agent.screen(client, "job desc", config)
    content = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert content[0]["text"] == "Head CV"
    assert content[0]["cache_control"] == {"type": "ephemeral"}
    assert content[1]["text"] == "Senior CV"
    assert content[1]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in content[2]   # volatile job desc — no cache

def test_cover_letter_returns_text(config):
    ai_agent.cv_cache["head_of_it"] = "Head CV"
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text="Dear Hiring Manager, ...")]
    client = MagicMock()
    client.messages.create.return_value = mock_resp
    result = ai_agent.cover_letter(client, "job desc", "head_of_it", "PT X", "CTO", config)
    assert result == "Dear Hiring Manager, ..."

def test_cover_letter_sends_selected_cv_with_cache_control(config):
    ai_agent.cv_cache["senior_engineer"] = "Senior CV"
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text="Letter")]
    client = MagicMock()
    client.messages.create.return_value = mock_resp
    ai_agent.cover_letter(client, "job desc", "senior_engineer", "PT Y", "Engineer", config)
    content = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert content[0]["text"] == "Senior CV"
    assert content[0]["cache_control"] == {"type": "ephemeral"}
