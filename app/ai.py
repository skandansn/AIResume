import google.generativeai as genai
from inputFiles import ai_prompt as ai_prompts
from resume_writer import update_resume_for_job_description
from config.app_configs import settings
from firebase_utils import firebase_get_user_from_firestore

def call_ai_and_get_response_text(prompt):
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

def generate_keywords_matched_resume(user_id, description, input_keywords, tex_file_name):
    keywords = ""
    if input_keywords.optional_keywords:
        keywords = generate_keywords_from_job_description(description)
    if input_keywords.mandatory_keywords is not None:
        must_keywords = "These keywords are mandatory and they HAVE to be in the resume: " + input_keywords.mandatory_keywords + "\n"
        if keywords == "":
            keywords = must_keywords
        else:
            other_keywords = "These keywords are also important and so, try to add them in the resume: " + keywords + "\n"
            keywords = must_keywords + other_keywords
    if input_keywords.ignore_keywords is not None:
        ignore_keywords = "I do not possess these particular skills. So always ignore these keywords: " + input_keywords.ignore_keywords + "\n"
        keywords = keywords + ignore_keywords

    user_data = firebase_get_user_from_firestore(user_id)

    prompt = ai_prompts.inject_keywords_into_resume_prompt + keywords + user_data.get("resume_content")
    response = call_ai_and_get_response_text(prompt)
    resume_names = {"tex_file_name": tex_file_name, "output_resume_name": user_data.get("output_resume_name"), "user_id": user_id}
    return update_resume_for_job_description(response, resume_names)

def generate_keywords_from_job_description(description):
    prompt = ai_prompts.extract_keywords_from_job_description_prompt + description
    return call_ai_and_get_response_text(prompt)





        



    