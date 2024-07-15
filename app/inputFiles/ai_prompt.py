extract_keywords_from_job_description_prompt = """
    You are an expert in understanding the job description and extracting the technical key words from the given software or tech job description.
    I will give you the job description.
    You will read it and find the technical key words that are in the description and qualifications sections of the job description.
    You will return the technical key words that you found in the job description, separated by commas.

    The job description is given below: \n
"""

inject_keywords_into_resume_prompt = """
    You are a expert in editing tech resume and you do not use any formatting. You only add the key words in the resume. 
    I will give you my current resume's SkillsSection, ExperienceSection and ProjectsSection.
    I will also give you the key words that I need to be included in my current resume.
    You will need to do the following things.
    i) Read and understand my resume data.
    ii) Among the key words given, find the important key words that are missing in my resume.
    iii) Add those key words in the resume in such a way that my resume has all those important missing key words explictly mentioned, spread out throughout skills, experience and projects sections.
    Make sure to add each keyword only once.
    You are only a top level editor if you do not change the format of the resume. Do not add any other formatting or bold or *text* or **text** or italic to the final text.
    Give me the final updated resume which has the key words added in the same format as the input.

    The key words are given below: \n
"""

whole_resume_prompts = [extract_keywords_from_job_description_prompt, inject_keywords_into_resume_prompt]