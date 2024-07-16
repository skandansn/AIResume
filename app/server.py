import fastapi
import pydanticModels.input_models as input_models
from ai import generate_keywords_matched_resume

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"Automated Resume Parser is running!"}

@app.post("/keywordsInjections/jobDescription")
def job_description_injections(input: input_models.JobDescription):
    if input.keywords.mandatory_keywords is None and input.keywords.optional_keywords == False:
        return "Please provide at least keywords.mandatory_keywords or set keywords.optional_keywords to true"
    if input.resume_name == "":
        return "Please provide a resume name"
    return generate_keywords_matched_resume(input.description, input.keywords, input.resume_name)
    