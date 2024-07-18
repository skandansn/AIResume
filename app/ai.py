import os
import google.generativeai as genai
from inputFiles import ai_prompt as ai_prompts
from inputFiles import resume_data as resume_data
from resume_writer import update_resume_for_job_description


def call_ai_and_get_response_text(prompt):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(prompt)
    return response.text

def generate_keywords_matched_resume(description, input_keywords, resume_name):
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
    prompt = ai_prompts.inject_keywords_into_resume_prompt + keywords + resume_data.whole_resume_data 
    response = call_ai_and_get_response_text(prompt)
    return update_resume_for_job_description(response, resume_name)

def generate_keywords_from_job_description(description):
    prompt = ai_prompts.extract_keywords_from_job_description_prompt + description
    return call_ai_and_get_response_text(prompt)





        



    