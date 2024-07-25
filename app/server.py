import fastapi
from typing import Annotated
from fastapi import Depends, UploadFile, File
import pydanticModels.input_models as input_models
from starlette.responses import JSONResponse
from ai import generate_keywords_matched_resume
from account import get_output_resume_link, sign_up_with_email_and_password, sign_in_with_email_and_password, update_output_resume_name, update_resume_content, get_user_data, update_input_tex, get_tex_files
from fastapi.middleware.cors import CORSMiddleware
from middleware.authentication_middleware import get_firebase_user_from_token
from middleware.logging_middleware import LoggingMiddleware
from middleware.exception_handling_middleware import ExceptionHandlingMiddleware

app = fastapi.FastAPI()

origins = [
    "http://localhost:3000",
    "https://airesume-frontend.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

app.add_middleware(ExceptionHandlingMiddleware)

@app.get("/")
def read_root():
    return {"AIResume is running!"}

@app.post("/keywordsInjections/jobDescription")
def job_description_injections(user: Annotated[dict, Depends(get_firebase_user_from_token)], input: input_models.JobDescription):
    if input.keywords.mandatory_keywords is None and input.keywords.optional_keywords == False:
        return "Please provide at least keywords.mandatory_keywords or set keywords.optional_keywords to true"
    if input.resume_name == "":
        return "Please provide a resume name"
    return generate_keywords_matched_resume(user.get("user_id"), input.description, input.keywords, input.resume_name)

@app.post("/signUp")
def sign_up(input: input_models.SignUp, response: fastapi.Response):
    user = sign_up_with_email_and_password(input.email, input.password)
    token = user.get("idToken")
    response.set_cookie(key="authToken", value=token, httponly=True)
    return user

@app.post("/signIn")
def sign_in(input: input_models.SignUp, response: fastapi.Response):
    user = sign_in_with_email_and_password(input.email, input.password)
    token = user.get("idToken")
    response.set_cookie(key="authToken", value=token, httponly=True, samesite="lax", secure=True)
    return user

@app.post("/signOut")
def sign_out(user: Annotated[dict, Depends(get_firebase_user_from_token)], response: fastapi.Response):
    response.set_cookie(key="authToken", value="", httponly=True, expires=0, max_age=0)
    return user

@app.post("/account/updateOutputResumeName")
def output_resume_name_update(user: Annotated[dict, Depends(get_firebase_user_from_token)], resume_name: input_models.UpdateResumeName):
    return update_output_resume_name(user, resume_name.resume_name)

@app.post("/account/updateResumeContent")
def resume_content_update(user: Annotated[dict, Depends(get_firebase_user_from_token)], resume_content: input_models.ResumeContent):
    return update_resume_content(user, resume_content.resume_content)

@app.post("/account/updateInputTex")
async def input_tex_update(user: Annotated[dict, Depends(get_firebase_user_from_token)], input_tex: UploadFile = File(...)):
    file = {}
    file["filename"] = input_tex.filename
    file["content"] = await input_tex.read()
    return update_input_tex(user, file)

@app.get("/account/listTexFiles")
def tex_files_list(user: Annotated[dict, Depends(get_firebase_user_from_token)]):
    return get_tex_files(user)

@app.get("/account")
def account_info(user: Annotated[dict, Depends(get_firebase_user_from_token)]):
    return get_user_data(user)

@app.get("/account/outputResumeLink")
def output_resume_link(user: Annotated[dict, Depends(get_firebase_user_from_token)]):
    return get_output_resume_link(user)