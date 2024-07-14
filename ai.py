import google.generativeai as genai
import os
from resume_writer import update_resume
from input.resume_data import resume_data
from input.ai_prompt import ai_input_prompt

def ai_generate_keyworded_resume(keywords):    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')


    base_prompt = ai_input_prompt

    resume = resume_data

    keywords = """ \n \n The keywords are given below: """ + ",".join(keywords) + "\n"

    complete_prompt = base_prompt + keywords + resume 

    # print(complete_prompt)

    response = model.generate_content(complete_prompt)

    # print(response.text)

    return update_resume(response.text)







        



    