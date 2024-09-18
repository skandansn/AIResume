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
    iii) Add those key words in the resume in such a way that my resume has all those important missing key words explictly mentioned, spread out throughout SkillsSection, ExperienceSection and ProjectsSection.
    iv) Try to add the keywords as part of an existing sentence or bullet point in the resume. If you cannot find a suitable place to add the keyword, add a new bullet point with the keyword.
    Make sure to add each keyword only once.
    Give me the final updated resume which has the key words added in the same format as the input.

    The key words are given below: \n
"""

whole_resume_prompts = [extract_keywords_from_job_description_prompt, inject_keywords_into_resume_prompt]