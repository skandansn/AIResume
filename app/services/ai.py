import time

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from fastapi import HTTPException
from pydantic import ValidationError
from inputFiles import ai_prompt as ai_prompts
from middleware.logging_middleware import logger
from models.ai_models import ExtractedKeywords, ParsedResume, TailoredResume
from config.app_configs import settings
from .resume_writer import (
    build_coverage_report,
    parse_resume_sections,
    render_resume_sections_for_prompt,
    write_resume_from_tailored,
)
from .firebase_utils import firebase_get_user_from_firestore

# Editing a resume is a fidelity task, not a creative one, so the sampling stays
# tight and the same input gives the same output.
TEMPERATURE = 0.3
SEED = 7
REQUEST_TIMEOUT_MS = 120_000
RETRY_PAUSE_SECONDS = 1.5

def _client():
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
    )

def call_ai_and_get_response_text(prompt, system_instruction=None):
    """Plain text generation. Kept for callers that do not need a schema."""
    response = _client().models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=TEMPERATURE,
            seed=SEED,
            system_instruction=system_instruction,
        ),
    )
    return response.text

def call_ai_for_model(prompt, schema, system_instruction=None, attempts=2):
    """Generation with a response schema, retried if the model returns something
    that does not fit it, or if the call to the model does not complete."""
    last_error = None
    unusable = "The AI returned something unusable. Please try again."

    for attempt in range(attempts):
        if attempt > 0:
            time.sleep(RETRY_PAUSE_SECONDS)

        try:
            response = _client().models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    seed=SEED + attempt,
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )

            parsed = response.parsed
            if parsed is None:
                parsed = schema.model_validate_json(response.text)

            return parsed
        except (ValidationError, ValueError) as e:
            last_error = e
            logger.error("model response did not fit %s on attempt %s: %s", schema.__name__, attempt + 1, e)
        except (httpx.TransportError, genai_errors.ServerError) as e:
            # the connection to the model drops often enough to be worth riding
            # out, and it says nothing about the request itself
            last_error = e
            unusable = "The AI service did not respond. Please try again in a moment."
            logger.error("call to the model failed on attempt %s: %s", attempt + 1, e)

    raise HTTPException(status_code=502, detail=unusable) from last_error

def extract_keywords_from_job_description(description):
    """The skills a posting screens for, so the candidate can confirm which ones
    they can honestly claim before anything is written."""
    if not description or not description.strip():
        raise HTTPException(status_code=400, detail="Please paste the job posting first")

    result = call_ai_for_model(
        ai_prompts.extract_keywords_prompt + description.strip(),
        ExtractedKeywords,
    )

    seen = set()
    keywords = []
    for keyword in result.keywords:
        cleaned = keyword.strip()
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            keywords.append(cleaned)

    return keywords

def generate_keywords_matched_resume(user, description, input_keywords, tex_file_name, approved_keywords=None):
    """Builds a tailored resume. Returns (pdf_bytes, output_resume_name, report)."""
    user_data = firebase_get_user_from_firestore(user)

    if not user_data or not user_data.get("resume") or not user_data.get("resume").get("content"):
        raise HTTPException(status_code=400, detail="Please save your resume details before generating a resume")

    output_resume_name = user_data.get("output_resume_name")
    if not output_resume_name:
        raise HTTPException(status_code=400, detail="Please set a name for your resume file before generating a resume")

    resume_label_count = user_data.get("resume").get("label_count")
    found_tex_file = False
    for tex_file in user_data.get("tex_files") or []:
        if tex_file.get("file_name") == tex_file_name:
            if tex_file.get("label_count") != resume_label_count:
                raise HTTPException(status_code=400, detail="Please update the resume content to match the tex file or select another valid tex file")
            found_tex_file = True
            break

    if not found_tex_file:
        raise HTTPException(status_code=400, detail="Tex file not found. Please select a valid tex file")

    parsed = parse_resume_sections(user_data.get("resume").get("content"))

    # ticking a skill is the candidate saying they have it, so those are taken at
    # their word. skills the model picks out of the posting still have to be
    # supported by what the resume already describes.
    confirmed = [k.strip() for k in (approved_keywords or []) if k and k.strip()]
    suggested = []
    if not confirmed and input_keywords.optional_keywords:
        suggested = extract_keywords_from_job_description(description)

    keywords = confirmed + suggested

    prompt = ai_prompts.build_tailor_prompt(
        job_description=description,
        confirmed=confirmed,
        suggested=suggested,
        resume_sections=render_resume_sections_for_prompt(parsed),
        block_counts={"experience": len(parsed["experience"]), "projects": len(parsed["projects"])},
    )
    prompt += ai_prompts.build_required_instruction(input_keywords.mandatory_keywords)
    prompt += ai_prompts.build_avoid_instruction(input_keywords.ignore_keywords)

    tailored = call_ai_for_model(
        prompt,
        TailoredResume,
        system_instruction=ai_prompts.resume_editor_system_instruction,
    )

    resume_names = {"tex_file_name": tex_file_name, "output_resume_name": output_resume_name}
    pdf = write_resume_from_tailored(tailored, resume_names, user)

    # what the candidate asked for by hand counts towards coverage too
    by_hand = [k.strip() for k in (input_keywords.mandatory_keywords or "").split(",") if k.strip()]
    checked = list(keywords) + by_hand

    # a skill the candidate vouched for is never "left out on purpose". if one
    # did not make it, that is a gap they should see, not an excuse they read.
    # skills the model suggested itself may still be skipped with a reason.
    insisted = {k.lower() for k in confirmed + by_hand}
    skipped = [item for item in tailored.keywords_skipped if item.keyword.strip().lower() not in insisted]

    report = build_coverage_report(pdf, checked, skipped)

    return pdf, output_resume_name, report


# a resume is long, and only the first pages of one are ever the resume
MAX_RESUME_CHARACTERS = 20000

def read_resume_from_text(text):
    """Turns the text of a resume the candidate already has into form fields."""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="That file had no text in it. Try another file, or type your details in.")

    if len(text.strip()) < 120:
        raise HTTPException(
            status_code=400,
            detail="There was hardly any text in that file. If it is a scan, the words are pictures rather than text.",
        )

    return call_ai_for_model(
        ai_prompts.read_resume_prompt + text.strip()[:MAX_RESUME_CHARACTERS],
        ParsedResume,
        system_instruction=ai_prompts.read_resume_system_instruction,
    )

def generate_keywords_from_job_description(description):
    """Kept for backwards compatibility; returns a comma separated string."""
    return ", ".join(extract_keywords_from_job_description(description))
