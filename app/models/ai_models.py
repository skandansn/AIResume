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


# ---- reading an existing resume so the form can be filled in for the user ----


class ParsedSkillGroup(BaseModel):
    category: str = Field(description="The heading this group of skills sits under, for example 'Languages'.")
    skills: str = Field(description="The skills in that group, comma separated.")


class ParsedExperience(BaseModel):
    role: str = Field(description="Job title, exactly as written.")
    company: str = Field(description="Employer name, exactly as written.")
    location: str = Field(default="", description="City and state or country, if given.")
    start_date: str = Field(default="", description="Start date as written, for example 'Jun 2023'.")
    end_date: str = Field(default="", description="End date as written, or 'Present'.")
    bullets: List[str] = Field(description="One entry per bullet point, copied word for word.")


class ParsedProject(BaseModel):
    name: str = Field(description="Project name, exactly as written.")
    url: str = Field(default="", description="Link to the project, if one is given.")
    bullets: List[str] = Field(description="One entry per bullet point, copied word for word.")


class ParsedEducation(BaseModel):
    school: str = Field(description="Institution name.")
    location: str = Field(default="", description="City and state or country, if given.")
    degree: str = Field(default="", description="Degree and field, for example 'B.S. in Computer Science'.")
    graduation: str = Field(default="", description="Graduation date as written.")
    detail: str = Field(default="", description="Anything shown alongside, such as a GPA.")


class ParsedResume(BaseModel):
    """A resume read back out of a file the candidate already had."""

    full_name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""
    skills: List[ParsedSkillGroup] = []
    experience: List[ParsedExperience] = []
    projects: List[ParsedProject] = []
    education: List[ParsedEducation] = []
    extras: List[str] = Field(default=[], description="Awards, publications and anything else, one line each.")
