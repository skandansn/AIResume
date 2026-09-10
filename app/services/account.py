from .firebase_utils import *
from .resume_writer import calculate_input_tex_label_count, get_named_section_from_ai_response, split_section_into_section_items

def sign_up_with_email_and_password(email, password):
    user = firebase_sign_up_with_email_and_password(email, password)
    firebase_create_user_in_firestore(user, email)
    return user

def sign_in_with_email_and_password(email, password):
    return firebase_sign_in_with_email_and_password(email, password)

def update_output_resume_name(user, resume_name):
    if resume_name == "" or resume_name is None or resume_name.isspace():
        raise HTTPException(status_code=400, detail="Resume name cannot be empty")
    firebase_update_output_resume_name(user, resume_name)
    return True

def update_resume_content(user, resume_content):
    section_items_count = verify_resume_content_format(resume_content)
    firebase_update_resume_content(user, resume_content, section_items_count)
    return True

# the form as the browser holds it. the resume text and the template are both
# derived from it and neither can be turned back into it, so without this the
# only copy would live in one browser
MAX_PROFILE_CHARACTERS = 200000

def update_profile(user, profile_json):
    if not profile_json or not profile_json.strip():
        raise HTTPException(status_code=400, detail="Profile cannot be empty")

    if len(profile_json) > MAX_PROFILE_CHARACTERS:
        raise HTTPException(status_code=400, detail="That is too much detail to store. Please shorten your resume.")

    firebase_update_user_document(user, {"profile": profile_json})
    return True

def get_user_data(user):
    data = firebase_get_user_from_firestore(user)
    if data is None:
        return data
    # the templates carry their whole .tex with them now, which callers do not
    # need, so hand back just the parts that describe them
    return {**data, "tex_files": without_tex_content(data.get("tex_files"))}

def get_output_resume_name(user):
    return firebase_get_output_resume_name(user)

def get_resume_content(user):
    return firebase_get_resume_content(user)

def get_tex_files(user):
    return without_tex_content(firebase_get_tex_files(user))

def without_tex_content(tex_files):
    """Describes each template without shipping its whole .tex to the client.

    Templates saved before the move off file storage have no content stored, so
    has_content lets the client steer those users back to saving rather than
    letting them try to generate and fail.
    """
    if not tex_files:
        return tex_files

    return [
        {
            **{key: value for key, value in tex_file.items() if key != "content"},
            "has_content": bool(tex_file.get("content")),
        }
        for tex_file in tex_files
    ]

def update_input_tex(user, input_tex):
    label_count = calculate_input_tex_label_count(input_tex["content"])
    firebase_add_resume_tex_file_to_existing_tex_files(
        user,
        input_tex["filename"],
        label_count,
        input_tex["content"].decode("utf-8"),
    )
    return True

def verify_resume_content_format(resume_content):
    if resume_content == "" or resume_content is None or resume_content.isspace():
        raise HTTPException(status_code=400, detail="Resume content cannot be empty")

    mandatory_section_words = ["SkillsSectionStart", "SkillsSectionEnd", "ExperienceSectionStart", "ExperienceSectionEnd", "ProjectsSectionStart", "ProjectsSectionEnd"]
    if not all(word in resume_content for word in mandatory_section_words):
        raise HTTPException(status_code=400, detail="Please provide all mandatory sections in the resume content. "+ str(mandatory_section_words))

    resume_content_list = resume_content.split("\n")

    # either section may be empty. a career changer with no projects and a
    # student with no jobs both need a resume, so only the pair being empty is
    # a problem: there would be nothing to tailor
    experience_section = get_named_section_from_ai_response(resume_content_list, "ExperienceSectionStart", "ExperienceSectionEnd")
    projects_section = get_named_section_from_ai_response(resume_content_list, "ProjectsSectionStart", "ProjectsSectionEnd")

    section_items = []
    split_section_into_section_items(section_items, experience_section)
    split_section_into_section_items(section_items, projects_section)

    if len(section_items) == 0:
        raise HTTPException(status_code=400, detail="Please add at least one role or one project")

    return len(section_items) + 1 # +1 for skills section
