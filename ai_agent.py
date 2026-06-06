import json
from pypdf import PdfReader
from anthropic import Anthropic

CV_DISPLAY_NAMES: dict[str, str] = {
    "head_of_it": "Head of IT Developments",
    "senior_engineer": "Senior Software Engineer",
}

cv_cache: dict[str, str] = {}

_SCREENING_SYSTEM = (
    "You are a job screening assistant. Given two CVs and a job description, "
    "pick the better-fit CV and score the match. "
    "Respond ONLY with valid JSON: "
    '{"match_score": <0-100>, "cv_choice": "head_of_it" or "senior_engineer", "reason": "<one sentence>"}. '
    "Use head_of_it for leadership/strategy roles, senior_engineer for hands-on technical roles."
)

_COVER_LETTER_SYSTEM = (
    "You are a professional cover letter writer. "
    "Write a concise, tailored cover letter based on the provided CV and job description. "
    "Return plain text only — no markdown, no subject line, no date."
)

def load_cv_cache(config: dict) -> None:
    for key, path in config["cv"].items():
        reader = PdfReader(path)
        cv_cache[key] = "\n".join(page.extract_text() or "" for page in reader.pages)

def screen(client: Anthropic, job_description: str, config: dict) -> dict:
    cv_blocks = [
        {"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}
        for text in cv_cache.values()
    ]
    response = client.messages.create(
        model=config["ai"]["screening_model"],
        system=[{"type": "text", "text": _SCREENING_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": [
            *cv_blocks,
            {"type": "text", "text": f"Job to screen:\n{job_description}"},
        ]}],
        max_tokens=256,
    )
    return json.loads(response.content[0].text)

def cover_letter(client: Anthropic, job_description: str, cv_choice: str,
                 company: str, title: str, config: dict) -> str:
    response = client.messages.create(
        model=config["ai"]["cover_letter_model"],
        system=[{"type": "text", "text": _COVER_LETTER_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": [
            {"type": "text", "text": cv_cache[cv_choice], "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": (
                f"Company: {company}\nRole: {title}\n\n"
                f"Job description:\n{job_description}\n\n"
                "Write a cover letter for this role."
            )},
        ]}],
        max_tokens=1024,
    )
    return response.content[0].text
