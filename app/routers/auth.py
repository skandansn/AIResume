from fastapi import APIRouter, Depends, Response
from models import input_models
from typing import Annotated
from services.account import sign_up_with_email_and_password, sign_in_with_email_and_password
from dependencies import get_firebase_user_from_token


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/signUp")
def sign_up(input: input_models.SignUp, response: Response):
    user = sign_up_with_email_and_password(input.email, input.password)
    token = user.get("idToken")
    response.delete_cookie("authToken")
    response.set_cookie(key="authToken", value=token, httponly=True, samesite="none", secure=True)
    return user

@router.post("/signIn")
def sign_in(input: input_models.SignUp, response: Response):
    user = sign_in_with_email_and_password(input.email, input.password)
    token = user.get("idToken")
    response.delete_cookie("authToken")
    response.set_cookie(key="authToken", value=token, httponly=True, samesite="none", secure=True)
    return user

@router.post("/signOut")
def sign_out(user: Annotated[dict, Depends(get_firebase_user_from_token)], response: Response):
    response.set_cookie(key="authToken", value="", httponly=True, expires=0, max_age=0)
    return user

