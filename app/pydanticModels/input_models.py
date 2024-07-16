from pydantic import BaseModel
from typing import Optional

class Keywords(BaseModel):
    optional_keywords : bool = True
    mandatory_keywords : Optional[str] = None

class JobDescription(BaseModel):
    description : str
    keywords : Optional[Keywords] = None
    resume_name : Optional[str] = "whole_resume"

