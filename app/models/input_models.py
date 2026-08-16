from pydantic import BaseModel
from typing import List, Optional

class Keywords(BaseModel):
    optional_keywords : bool = True
    mandatory_keywords : Optional[str] = None
    ignore_keywords : Optional[str] = None

class JobDescription(BaseModel):
    description : str
    keywords : Keywords
    resume_name : Optional[str] = "whole_resume"
    # the skills the candidate confirmed they can claim. when present these are
    # used as they are, instead of asking the AI to pick keywords itself.
    approved_keywords : Optional[List[str]] = None

class JobDescriptionKeywords(BaseModel):
    description : str

class SignUp(BaseModel):
    email : str
    password : str

class UpdateResumeName(BaseModel):
    resume_name : str

class ResumeContent(BaseModel):
    resume_content : str
