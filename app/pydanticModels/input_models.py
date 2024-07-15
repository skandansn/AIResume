from pydantic import BaseModel
from typing import Optional

class JobDescription(BaseModel):
    description : str
    keywords : Optional[str] = None

