from firebase_utils import *

def sign_up_with_email_and_password(email, password):
    user = firebase_sign_up_with_email_and_password(email, password)
    firebase_create_user_in_firestore(user.get("localId"), email)
    return user
    
def sign_in_with_email_and_password(email, password):
    return firebase_sign_in_with_email_and_password(email, password)

def update_output_resume_name(user, resume_name):
    firebase_update_output_resume_name(user.get("user_id"), resume_name)
    return True

def update_resume_content(user, resume_content):
    firebase_update_resume_content(user.get("user_id"), resume_content)
    return True

def get_user_data(user):
    return firebase_get_user_from_firestore(user.get("user_id"))

def get_output_resume_name(user):
    return firebase_get_output_resume_name(user.get("user_id"))

def get_resume_content(user):
    return firebase_get_resume_content(user.get("user_id"))

def get_output_resume_link(user):
    output_resume_name = get_output_resume_name(user)
    if output_resume_name == "" or output_resume_name is None:
        raise HTTPException(status_code=400, detail="Output resume name not set. Please set") 
    return firebase_download_file_url(user.get("user_id") + "/" + get_output_resume_name(user)+".pdf")

def get_tex_files(user):
    return firebase_get_tex_files(user.get("user_id"))

def update_input_tex(user, input_tex):
    url = firebase_upload_file(input_tex["content"], user.get("user_id") + "/" + input_tex["filename"])
    firebase_add_resume_tex_file_to_existing_tex_files(user.get("user_id"), input_tex["filename"])
    return url
