from pydantic import BaseModel, Field
from typing import List

# These models are handed to Gemini as a response schema, so the model returns
# parseable JSON instead of marker delimited text. The docstrings and field
# descriptions are part of the prompt from the model's point of view, so they
# are written to be read by it.


class TailoredSkillGroup(BaseModel):
    category: str = Field(description="The skill group label, exactly as it was given, for example 'Languages'.")
    values: str = Field(description="Comma separated skills for this group.")


class TailoredBlock(BaseModel):
    heading: str = Field(description="The heading line of this block, copied exactly as it was given.")
    bullets: List[str] = Field(description="One rewritten bullet point per entry. No bullet characters or numbering.")


class SkippedKeyword(BaseModel):
    keyword: str = Field(description="A keyword from the job posting that was not added.")
    reason: str = Field(
        description="Short, plain explanation of why it was left out, addressed to the candidate. "
        "For example 'Nothing in your experience supports this'."
    )


class TailoredResume(BaseModel):
    skills: List[TailoredSkillGroup] = Field(description="The skills section, in the same order and grouping as the input.")
    experience: List[TailoredBlock] = Field(
        description="The experience blocks, same count and same order as the input. Never merge, drop, reorder or add blocks."
    )
    projects: List[TailoredBlock] = Field(
        description="The project blocks, same count and same order as the input. Never merge, drop, reorder or add blocks."
    )
    keywords_added: List[str] = Field(description="Keywords from the job posting that are now present in the resume.")
    keywords_skipped: List[SkippedKeyword] = Field(
        description="Keywords deliberately left out because the candidate's experience does not support them."
    )


class ExtractedKeywords(BaseModel):
    keywords: List[str] = Field(
        description="The concrete technical skills, tools and practices the posting asks for, most important first."
    )


class CoverageReport(BaseModel):
    """What actually made it into the finished PDF, checked against the PDF itself."""

    covered: List[str] = []
    missing: List[str] = []
    skipped: List[SkippedKeyword] = []
    page_count: int = 0
    text_is_extractable: bool = True


class TailoredResumeResponse(BaseModel):
    file_name: str
    pdf_base64: str
    report: CoverageReport
