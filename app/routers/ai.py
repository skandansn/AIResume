import base64
from fastapi import APIRouter, Depends, Request, HTTPException
from dependencies import get_firebase_user_from_token
from services.ai import extract_keywords_from_job_description, generate_keywords_matched_resume
from models import input_models
from models.ai_models import ExtractedKeywords, TailoredResumeResponse

router = APIRouter(
    prefix = "/keywordsInjections",
    tags = ["keywordsInjections"],
    dependencies=[Depends(get_firebase_user_from_token)],
    responses={404: {"description": "Not found"}},
)

@router.post("/extractKeywords", response_model=ExtractedKeywords)
def job_description_keywords(input: input_models.JobDescriptionKeywords):
    """The skills a posting screens for, so the candidate can confirm which ones
    they can actually claim before the resume is written."""
    return ExtractedKeywords(keywords=extract_keywords_from_job_description(input.description))

@router.post("/jobDescription", response_model=TailoredResumeResponse)
def job_description_injections(request:Request, input: input_models.JobDescription):
    has_keywords = bool(input.approved_keywords) or input.keywords.mandatory_keywords is not None

    if not has_keywords and input.keywords.optional_keywords == False:
        raise HTTPException(status_code=400, detail="Please provide at least keywords.mandatory_keywords or set keywords.optional_keywords to true")
    if input.resume_name == "":
        raise HTTPException(status_code=400, detail="Please provide a resume name")
    if input.description == "" and not has_keywords and input.keywords.optional_keywords == True:
        raise HTTPException(status_code=400, detail="Please provide a job description if you want to use optional AI keywords")

    pdf, output_resume_name, report = generate_keywords_matched_resume(
        request.state.logged_in_user,
        input.description,
        input.keywords,
        input.resume_name,
        input.approved_keywords,
    )

    # the PDF travels in the response instead of being uploaded, and rides along
    # with the report so the client can show what actually landed in it
    return TailoredResumeResponse(
        file_name=f"{output_resume_name}.pdf",
        pdf_base64=base64.b64encode(pdf).decode("ascii"),
        report=report,
    )
