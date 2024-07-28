from firebase_utils import *
from resume_writer import calculate_input_tex_label_count, get_named_section_from_ai_response, split_section_into_section_items

def sign_up_with_email_and_password(email, password):
    user = firebase_sign_up_with_email_and_password(email, password)
    firebase_create_user_in_firestore(user.get("localId"), email)
    return user
    
def sign_in_with_email_and_password(email, password):
    return firebase_sign_in_with_email_and_password(email, password)

def update_output_resume_name(user, resume_name):
    if resume_name == "" or resume_name is None or resume_name.isspace():
        raise HTTPException(status_code=400, detail="Resume name cannot be empty")
    firebase_update_output_resume_name(user.get("user_id"), resume_name)
    return True

def update_resume_content(user, resume_content):
    section_items_count = verify_resume_content_format(resume_content)
    firebase_update_resume_content(user.get("user_id"), resume_content, section_items_count)
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
    label_count = calculate_input_tex_label_count(input_tex["content"])
    url = firebase_upload_file(input_tex["content"], user.get("user_id") + "/" + input_tex["filename"])
    firebase_add_resume_tex_file_to_existing_tex_files(user.get("user_id"), input_tex["filename"], label_count)
    return url

def verify_resume_content_format(resume_content):
    if resume_content == "" or resume_content is None or resume_content.isspace():
        raise HTTPException(status_code=400, detail="Resume content cannot be empty")

    mandatory_section_words = ["SkillsSectionStart", "SkillsSectionEnd", "ExperienceSectionStart", "ExperienceSectionEnd", "ProjectsSectionStart", "ProjectsSectionEnd"]
    if not all(word in resume_content for word in mandatory_section_words):
        raise HTTPException(status_code=400, detail="Please provide all mandatory sections in the resume content. "+ str(mandatory_section_words))
    
    resume_content_list = resume_content.split("\n")
    
    experience_section = get_named_section_from_ai_response(resume_content_list, "ExperienceSectionStart", "ExperienceSectionEnd")
    if len(experience_section) == 0:
        raise HTTPException(status_code=400, detail="Experience section cannot be empty")
    
    projects_section = get_named_section_from_ai_response(resume_content_list, "ProjectsSectionStart", "ProjectsSectionEnd")
    if len(projects_section) == 0:
        raise HTTPException(status_code=400, detail="Projects section cannot be empty")
    
    section_items = []
    split_section_into_section_items(section_items, experience_section)
    split_section_into_section_items(section_items, projects_section)

    if len(section_items) == 0:
        raise HTTPException(status_code=400, detail="Experience and Projects sections cannot be empty")
    
    return len(section_items) + 1 # +1 for skills section

    

            
    
    
    

    

    
    