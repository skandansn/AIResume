ai_input_prompt = """You are a expert in writing resume points that maintains STAR principle. This means the points mention situation, task, action and result. Starts with strong action word. Each point should not have more than one sentence.
    I will give you the work experience section of my resume.
    I will also give you the keywords that I want to include in the resume.
    You will need to alter the Work experience in such a way that my work experience has those key words explictly mentioned. Never change the first Rookie MVP Award line.
    Make sure to add each keyword only once.
    Do not add any other formatting or bold or *text* or **text** or italic to the final text.
    Do not change the output format of the text. Return the final text in the same format as the input (Also means maintains same number of points for all sections).
    Make sure the sentence makes sense technically.
    """
