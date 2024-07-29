from fastapi import APIRouter, Depends, Request
from dependencies import get_firebase_user_from_token
from services.ai import generate_keywords_matched_resume
from models import input_models

router = APIRouter(
    prefix = "/keywordsInjections",
    tags = ["keywordsInjections"],
    dependencies=[Depends(get_firebase_user_from_token)],
    responses={404: {"description": "Not found"}},
)

@router.post("/jobDescription")
def job_description_injections(request:Request, input: input_models.JobDescription):
    if input.keywords.mandatory_keywords is None and input.keywords.optional_keywords == False:
        return "Please provide at least keywords.mandatory_keywords or set keywords.optional_keywords to true"
    if input.resume_name == "":
        return "Please provide a resume name"
    if input.description == "" and input.keywords.optional_keywords == True:
        return "Please provide a job description if you want to use optional AI keywords"
    return generate_keywords_matched_resume(request.state.logged_in_user.get("user_id"), input.description, input.keywords, input.resume_name)