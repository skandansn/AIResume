import fastapi
import pydanticModels.input_models as input_models
from ai import generate_keywords_matched_resume

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"Automated Resume Parser is running!"}

@app.post("/keywordsInjections/jobDescription")
def job_description_injections(input: input_models.JobDescription):
    return generate_keywords_matched_resume(input.description)