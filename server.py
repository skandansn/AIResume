import fastapi
from pydantic import BaseModel
from ai import ai_generate_keyworded_resume

class Keywords(BaseModel):
    keywords : list[str]


app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"Automated Resume Parser is running!"}

@app.post("/keywordsInjections")
def keyword_injections(input: Keywords):
    return ai_generate_keyworded_resume(input.keywords)
