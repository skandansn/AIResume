"""Covers the tailoring flow end to end with canned model responses.

Gemini is never called: `call_ai_for_model` is replaced, so these tests check the
wiring, the prompt that would have been sent, and the report that comes back.
"""
import io
import shutil

import pytest
from fastapi import HTTPException
from pypdf import PdfReader

from conftest import FIXTURES

from models.ai_models import ExtractedKeywords, TailoredResume
from models.input_models import Keywords
from services import ai as ai_service
from services import resume_writer
from test_resume_pipeline import STORED_CONTENT, tailored_resume

needs_pdflatex = pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex is not installed")

TEMPLATE = (FIXTURES / "frontend_template.tex").read_text(encoding="utf-8")

ACCOUNT = {
    "email": "someone@example.com",
    "output_resume_name": "Alex_Morgan_Resume",
    "resume": {"content": STORED_CONTENT, "label_count": 5},
    "tex_files": [{"file_name": "Alex_Template.tex", "label_count": 5}],
}


@pytest.fixture
def canned(monkeypatch):
    """Stubs Firestore and the model, and records the prompts that were built."""
    calls = []

    def fake_call(prompt, schema, system_instruction=None, attempts=2):
        calls.append({"prompt": prompt, "schema": schema, "system_instruction": system_instruction})

        if schema is ExtractedKeywords:
            return ExtractedKeywords(keywords=["Go", "Kubernetes", "Kafka", "Terraform"])
        if schema is TailoredResume:
            return tailored_resume()

        raise AssertionError(f"unexpected schema {schema}")

    monkeypatch.setattr(ai_service, "call_ai_for_model", fake_call)
    monkeypatch.setattr(ai_service, "firebase_get_user_from_firestore", lambda user: ACCOUNT)
    monkeypatch.setattr(resume_writer, "firebase_get_tex_file_content", lambda user, name: TEMPLATE)

    return calls


def generate(approved=None, keywords=None):
    return ai_service.generate_keywords_matched_resume(
        {"user_id": "u1", "logged_in_token": "t"},
        "Backend role building Go services on Kubernetes with Kafka and Terraform.",
        keywords or Keywords(optional_keywords=True),
        "Alex_Template.tex",
        approved,
    )


@needs_pdflatex
def test_generate_returns_pdf_name_and_report(canned):
    pdf, name, report = generate()

    assert pdf[:5] == b"%PDF-"
    assert name == "Alex_Morgan_Resume"
    assert report.page_count == 1
    assert set(report.covered) >= {"Go", "Kubernetes", "Kafka"}
    # the model said it could not support Terraform, and that is reported once,
    # as an explained omission rather than an unexplained gap
    assert report.skipped[0].keyword == "Terraform"
    assert "Terraform" not in report.missing
    assert "Terraform" not in report.covered


@needs_pdflatex
def test_approved_keywords_skip_the_extraction_call(canned):
    generate(approved=["Go", "PostgreSQL"])

    assert [call["schema"] for call in canned] == [TailoredResume]
    prompt = canned[0]["prompt"]
    assert "- Go" in prompt and "- PostgreSQL" in prompt
    assert "Kubernetes" not in prompt.split("<job_posting>")[0]


@needs_pdflatex
def test_without_approved_keywords_the_posting_is_read_first(canned):
    generate()

    assert [call["schema"] for call in canned] == [ExtractedKeywords, TailoredResume]


@needs_pdflatex
def test_prompt_carries_the_posting_the_rules_and_the_block_counts(canned):
    generate()

    tailor_call = canned[-1]
    prompt = tailor_call["prompt"]

    # the posting itself reaches the rewriting step, not just a keyword list
    assert "<job_posting>" in prompt
    assert "Kafka and Terraform" in prompt
    # the model is told exactly how many blocks to return
    assert "2 experience block(s)" in prompt
    assert "2 project block(s)" in prompt
    # and the honesty rules ride along as a system instruction
    assert "Never invent experience" in tailor_call["system_instruction"]


@needs_pdflatex
def test_ignore_and_mandatory_keywords_reach_the_prompt(canned):
    generate(keywords=Keywords(optional_keywords=True, mandatory_keywords="gRPC", ignore_keywords="PHP, Perl"))

    prompt = canned[-1]["prompt"]

    assert "gRPC" in prompt
    assert "does not have these skills" in prompt and "PHP, Perl" in prompt


@needs_pdflatex
def test_mandatory_keywords_are_checked_against_the_pdf(canned):
    _, _, report = generate(keywords=Keywords(optional_keywords=False, mandatory_keywords="Kubernetes, Rust"))

    assert "Kubernetes" in report.covered
    assert "Rust" in report.missing


def test_missing_resume_is_rejected(monkeypatch):
    monkeypatch.setattr(ai_service, "firebase_get_user_from_firestore", lambda user: {"email": "a@b.c"})

    with pytest.raises(HTTPException) as caught:
        generate()

    assert caught.value.status_code == 400
    assert "save your resume" in caught.value.detail


def test_missing_output_name_is_rejected(monkeypatch):
    monkeypatch.setattr(
        ai_service,
        "firebase_get_user_from_firestore",
        lambda user: {**ACCOUNT, "output_resume_name": None},
    )

    with pytest.raises(HTTPException) as caught:
        generate()

    assert caught.value.status_code == 400
    assert "name for your resume" in caught.value.detail


def test_label_count_mismatch_is_rejected(monkeypatch):
    monkeypatch.setattr(
        ai_service,
        "firebase_get_user_from_firestore",
        lambda user: {**ACCOUNT, "tex_files": [{"file_name": "Alex_Template.tex", "label_count": 9}]},
    )

    with pytest.raises(HTTPException) as caught:
        generate()

    assert caught.value.status_code == 400
    assert "match the tex file" in caught.value.detail


def test_unknown_template_is_rejected(monkeypatch):
    monkeypatch.setattr(ai_service, "firebase_get_user_from_firestore", lambda user: ACCOUNT)

    with pytest.raises(HTTPException) as caught:
        ai_service.generate_keywords_matched_resume(
            {"user_id": "u1"}, "jd", Keywords(), "does_not_exist.tex", ["Go"]
        )

    assert caught.value.status_code == 400
    assert "Tex file not found" in caught.value.detail


def test_extract_keywords_deduplicates_and_trims(monkeypatch):
    monkeypatch.setattr(
        ai_service,
        "call_ai_for_model",
        lambda *a, **k: ExtractedKeywords(keywords=[" Go ", "go", "Kafka", "", "Kafka"]),
    )

    assert ai_service.extract_keywords_from_job_description("a posting") == ["Go", "Kafka"]


def test_extract_keywords_needs_a_posting():
    with pytest.raises(HTTPException) as caught:
        ai_service.extract_keywords_from_job_description("   ")

    assert caught.value.status_code == 400
