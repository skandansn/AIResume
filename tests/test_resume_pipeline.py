"""Covers the fragile part of the pipeline: turning a tailored resume into a PDF.

The AI is never called. Model responses are canned, so these tests are free to
run and they fail loudly if the template filling, the LaTeX escaping or the PDF
verification breaks.

pdflatex has to be installed for the compiling tests.
"""
import io
import shutil

import pytest
from fastapi import HTTPException
from pypdf import PdfReader

from conftest import FIXTURES

from models.ai_models import SkippedKeyword, TailoredBlock, TailoredResume, TailoredSkillGroup
from services import resume_writer
from services.resume_writer import (
    build_coverage_report,
    latex_escape,
    parse_resume_sections,
    render_resume_sections_for_prompt,
    strip_latex,
    write_resume_from_tailored,
)

needs_pdflatex = pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex is not installed")

TEMPLATE = (FIXTURES / "frontend_template.tex").read_text(encoding="utf-8")

# what the frontend stores. the escaped "\$" is what older clients saved, and has
# to survive the round trip as a plain dollar sign.
STORED_CONTENT = """SkillsSectionStart

Languages: Python, TypeScript, Go
Frameworks: FastAPI, Next.js

SkillsSectionEnd

ExperienceSectionStart

Acme Corp - Senior Engineer:
Cut infrastructure spend by \\$2M while migrating billing to Go.
Reduced production incidents by 25\\% with contract tests.

Globex - Engineer:
Built an ingestion pipeline handling 2M events per day.

ExperienceSectionEnd

ProjectsSectionStart

Trailmix:
Built a trail finding app used by 800 hikers in its first month.

Note G:
Published an interactive notebook explaining the first algorithm.

ProjectsSectionEnd
"""


def tailored_resume(experience_blocks=2, project_blocks=2):
    """A canned model response shaped like the schema Gemini is asked for."""
    experience = [
        TailoredBlock(
            heading="Acme Corp - Senior Engineer",
            bullets=[
                "Cut infrastructure spend by $2M migrating billing services to Go on Kubernetes.",
                "Reduced production incidents by 25% with contract tests in CI/CD pipelines.",
            ],
        ),
        TailoredBlock(
            heading="Globex - Engineer",
            bullets=["Built an event-driven ingestion pipeline with Kafka handling 2M events per day."],
        ),
    ][:experience_blocks]

    projects = [
        TailoredBlock(
            heading="Trailmix",
            bullets=["Built a trail finding app on PostgreSQL used by 800 hikers in its first month."],
        ),
        TailoredBlock(
            heading="Note G",
            bullets=["Published an interactive notebook explaining the first published algorithm."],
        ),
    ][:project_blocks]

    return TailoredResume(
        skills=[
            TailoredSkillGroup(category="Languages", values="Python, TypeScript, Go"),
            TailoredSkillGroup(category="Frameworks", values="FastAPI, Next.js"),
            TailoredSkillGroup(category="Tools", values="Kubernetes, Kafka, PostgreSQL"),
        ],
        experience=experience,
        projects=projects,
        keywords_added=["Go", "Kubernetes", "Kafka", "PostgreSQL", "CI/CD"],
        keywords_skipped=[SkippedKeyword(keyword="Terraform", reason="Nothing in your experience supports this")],
    )


@pytest.fixture
def template(monkeypatch):
    monkeypatch.setattr(resume_writer, "firebase_get_tex_file_content", lambda user, name: TEMPLATE)


# ---------------------------------------------------------------- text handling

def test_latex_escape_escapes_each_special_once():
    assert latex_escape("Smith & Sons") == r"Smith \& Sons"
    assert latex_escape("cut cost $2M") == r"cut cost \$2M"
    assert latex_escape("100% of #tooling") == r"100\% of \#tooling"
    assert latex_escape("Engineer_II") == r"Engineer\_II"
    assert latex_escape("a\\b") == r"a\textbackslash{}b"
    # the braces introduced by an escape must not be escaped again
    assert latex_escape("~50 users") == r"\textasciitilde{}50 users"


def test_strip_latex_undoes_stored_escapes():
    assert strip_latex(r"cut cost \$2M by 25\%") == "cut cost $2M by 25%"
    assert strip_latex(r"\textasciitilde{}50 users") == "~50 users"


def test_parse_resume_sections_reads_headings_and_bullets():
    parsed = parse_resume_sections(STORED_CONTENT)

    assert [group["category"] for group in parsed["skills"]] == ["Languages", "Frameworks"]
    assert len(parsed["experience"]) == 2
    assert len(parsed["projects"]) == 2
    assert parsed["experience"][0]["heading"] == "Acme Corp - Senior Engineer"
    assert len(parsed["experience"][0]["bullets"]) == 2
    # stored escapes are gone by the time the model sees the text
    assert "$2M" in parsed["experience"][0]["bullets"][0]
    assert "\\" not in parsed["experience"][0]["bullets"][0]


def test_prompt_rendering_numbers_the_blocks():
    rendered = render_resume_sections_for_prompt(parse_resume_sections(STORED_CONTENT))

    assert "[1] Acme Corp - Senior Engineer" in rendered
    assert "[2] Globex - Engineer" in rendered
    assert "SkillsSectionStart" not in rendered


# ------------------------------------------------------------- template filling

@needs_pdflatex
def test_tailored_resume_compiles_and_keeps_its_content(template):
    pdf = write_resume_from_tailored(tailored_resume(), {"tex_file_name": "t.tex", "output_resume_name": "Test_Resume"}, {})

    assert pdf[:5] == b"%PDF-"

    reader = PdfReader(io.BytesIO(pdf))
    text = " ".join(page.extract_text() or "" for page in reader.pages)

    assert len(reader.pages) == 1
    # every block's bullets land, in the right place
    assert "migrating billing services to Go on Kubernetes" in text
    assert "Kafka handling 2M events per day" in text
    assert "800 hikers" in text
    assert "first published algorithm" in text
    # skills are inserted under the skills heading
    assert "Kubernetes, Kafka, PostgreSQL" in text
    # specials survive as themselves rather than as escapes
    assert "$2M" in text
    assert "25%" in text
    assert "textbackslash" not in text


@needs_pdflatex
def test_each_block_gets_its_own_bullets(template):
    """Guards the bug where duplicate labels gave two roles the same bullets."""
    pdf = write_resume_from_tailored(tailored_resume(), {"tex_file_name": "t.tex", "output_resume_name": "Test_Resume"}, {})
    text = " ".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf)).pages)

    assert text.count("2M events per day") == 1
    assert text.count("800 hikers") == 1


def test_block_count_mismatch_is_rejected(template):
    with pytest.raises(HTTPException) as caught:
        write_resume_from_tailored(
            tailored_resume(experience_blocks=1),
            {"tex_file_name": "t.tex", "output_resume_name": "Test_Resume"},
            {},
        )

    assert caught.value.status_code == 502


def test_missing_template_is_rejected(monkeypatch):
    monkeypatch.setattr(resume_writer, "firebase_get_tex_file_content", lambda user, name: None)

    with pytest.raises(HTTPException) as caught:
        write_resume_from_tailored(tailored_resume(), {"tex_file_name": "gone.tex", "output_resume_name": "R"}, {})

    assert caught.value.status_code == 400


# ---------------------------------------------------------------- verification

@needs_pdflatex
def test_coverage_report_reflects_the_pdf(template):
    pdf = write_resume_from_tailored(tailored_resume(), {"tex_file_name": "t.tex", "output_resume_name": "Test_Resume"}, {})

    report = build_coverage_report(
        pdf,
        ["Go", "Kubernetes", "Kafka", "Terraform", "Rust"],
        [SkippedKeyword(keyword="Terraform", reason="Nothing in your experience supports this")],
    )

    assert report.page_count == 1
    assert report.text_is_extractable
    assert set(report.covered) >= {"Go", "Kubernetes", "Kafka"}
    # keywords that are genuinely absent are reported as missing, not covered
    assert "Rust" in report.missing
    assert report.skipped[0].keyword == "Terraform"
    # one that was deliberately skipped is explained, not repeated as a gap
    assert "Terraform" not in report.missing


def test_coverage_report_survives_an_unreadable_pdf():
    report = build_coverage_report(b"not a pdf", ["Go"], [])

    assert report.text_is_extractable is False
    assert report.page_count == 0


# ------------------------------------------------------- legacy account data

def test_templates_saved_before_the_storage_move_are_flagged():
    """Old accounts have a template row with no .tex stored against it."""
    from services.account import without_tex_content

    described = without_tex_content([
        {"file_name": "old.tex", "label_count": 4},
        {"file_name": "new.tex", "label_count": 4, "content": TEMPLATE},
    ])

    assert described[0]["has_content"] is False
    assert described[1]["has_content"] is True
    # the .tex itself never goes back to the client
    assert "content" not in described[1]


# ------------------------------------------------------- optional sections

CONTENT_WITHOUT_PROJECTS = """SkillsSectionStart

Languages: Python, Go

SkillsSectionEnd

ExperienceSectionStart

Acme Corp - Senior Engineer:
Migrated billing to Go.

ExperienceSectionEnd

ProjectsSectionStart

ProjectsSectionEnd
"""


def test_a_resume_with_no_projects_is_accepted():
    from services.account import verify_resume_content_format

    # one experience block plus the skills section
    assert verify_resume_content_format(CONTENT_WITHOUT_PROJECTS) == 2


def test_a_resume_with_only_projects_is_accepted():
    """A student with no jobs yet still gets a resume."""
    from services.account import verify_resume_content_format

    content = """SkillsSectionStart

Languages: Python, Go

SkillsSectionEnd

ExperienceSectionStart

ExperienceSectionEnd

ProjectsSectionStart

Trailmix:
Built a trail finding app used by 800 hikers.

ProjectsSectionEnd
"""

    assert verify_resume_content_format(content) == 2


def test_a_resume_with_neither_is_rejected():
    from services.account import verify_resume_content_format

    empty = """SkillsSectionStart

Languages: Python

SkillsSectionEnd

ExperienceSectionStart

ExperienceSectionEnd

ProjectsSectionStart

ProjectsSectionEnd
"""

    with pytest.raises(HTTPException) as caught:
        verify_resume_content_format(empty)

    assert caught.value.status_code == 400
    assert "at least one role or one project" in caught.value.detail


def test_empty_sections_are_left_out_of_the_prompt():
    parsed = parse_resume_sections(CONTENT_WITHOUT_PROJECTS)

    assert parsed["projects"] == []

    rendered = render_resume_sections_for_prompt(parsed)

    assert "Experience:" in rendered
    assert "Projects:" not in rendered
