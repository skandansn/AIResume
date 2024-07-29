from fastapi import APIRouter, Depends, Request, Response
from dependencies import get_firebase_user_from_token
from typing import Annotated
from services.account import update_output_resume_name, update_resume_content, get_user_data, update_input_tex, get_tex_files, get_output_resume_link
from fastapi import UploadFile, File
from starlette.responses import JSONResponse
from models import input_models

router = APIRouter(
    prefix = "/account",
    tags = ["account"],
    dependencies=[Depends(get_firebase_user_from_token)],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
def account_info(request: Request):
    return get_user_data(request.state.logged_in_user)

@router.post("/updateOutputResumeName")
def output_resume_name_update(request:Request, resume_name: input_models.UpdateResumeName):
    return update_output_resume_name(request.state.logged_in_user, resume_name.resume_name)

@router.post("/updateResumeContent")
def resume_content_update(request:Request, resume_content: input_models.ResumeContent):
    return update_resume_content(request.state.logged_in_user, resume_content.resume_content)

@router.post("/updateInputTex")
async def input_tex_update(request:Request, input_tex: UploadFile = File(...)):
    if not input_tex.filename.endswith(".tex"):
        return JSONResponse(status_code=400, content={"message": "Please upload a .tex file"})
    file = {}
    file["filename"] = input_tex.filename
    file["content"] = await input_tex.read()
    return update_input_tex(request.state.logged_in_user, file)

@router.get("/listTexFiles")
def tex_files_list(request:Request):
    return get_tex_files(request.state.logged_in_user)

@router.get("/outputResumeLink")
def output_resume_link(request:Request):
    return get_output_resume_link(request.state.logged_in_user)




