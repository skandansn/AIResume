from pydantic import BaseModel
from typing import Optional

class Keywords(BaseModel):
    optional_keywords : bool = True
    mandatory_keywords : Optional[str] = None
    ignore_keywords : Optional[str] = None

class JobDescription(BaseModel):
    description : str
    keywords : Keywords
    resume_name : Optional[str] = "whole_resume"

class SignUp(BaseModel):
    email : str
    password : str

class UpdateResumeName(BaseModel):
    resume_name : str

class ResumeContent(BaseModel):
    resume_content : str

