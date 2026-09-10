"""Covers reading an existing resume into form fields, with a canned model."""
import pytest
from fastapi import HTTPException

from models.ai_models import ParsedExperience, ParsedResume, ParsedSkillGroup
from services import ai as ai_service

RESUME_TEXT = """Alex Morgan
alex@example.com | (555) 010-2030 | linkedin.com/in/alexmorgan

Skills
Languages: Python, Go
Frameworks: FastAPI, React

Experience
Software Engineer, Northwind Labs - Boston, MA        Jun 2023 - Present
Rebuilt the billing service in Python, cutting checkout errors by 30%.
Added integration tests across 6 services.
"""


@pytest.fixture
def canned(monkeypatch):
    calls = []

    def fake_call(prompt, schema, system_instruction=None, attempts=2):
        calls.append({"prompt": prompt, "schema": schema, "system_instruction": system_instruction})
        return ParsedResume(
            full_name="Alex Morgan",
            email="alex@example.com",
            skills=[ParsedSkillGroup(category="Languages", skills="Python, Go")],
            experience=[
                ParsedExperience(
                    role="Software Engineer",
                    company="Northwind Labs",
                    location="Boston, MA",
                    start_date="Jun 2023",
                    end_date="Present",
                    bullets=["Rebuilt the billing service in Python, cutting checkout errors by 30%."],
                )
            ],
        )

    monkeypatch.setattr(ai_service, "call_ai_for_model", fake_call)
    return calls


def test_the_resume_text_and_the_transcribing_rules_are_sent(canned):
    parsed = ai_service.read_resume_from_text(RESUME_TEXT)

    assert parsed.full_name == "Alex Morgan"
    assert parsed.experience[0].end_date == "Present"

    sent = canned[0]
    assert "Northwind Labs" in sent["prompt"]
    assert "Copy bullet points word for word" in sent["system_instruction"]
    assert "never invent" in sent["system_instruction"].lower()


def test_a_very_long_file_is_cut_down(canned):
    ai_service.read_resume_from_text(RESUME_TEXT + "x" * 50000)

    assert len(canned[0]["prompt"]) < ai_service.MAX_RESUME_CHARACTERS + 2000


def test_an_empty_file_is_rejected():
    with pytest.raises(HTTPException) as caught:
        ai_service.read_resume_from_text("   ")

    assert caught.value.status_code == 400
    assert "no text" in caught.value.detail


def test_a_scan_with_almost_no_text_is_rejected():
    """An image only PDF extracts to a few stray characters, not a resume."""
    with pytest.raises(HTTPException) as caught:
        ai_service.read_resume_from_text("Alex Morgan\nPage 1")

    assert caught.value.status_code == 400
    assert "scan" in caught.value.detail
