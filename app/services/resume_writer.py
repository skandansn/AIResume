from TexSoup import TexSoup
from pdflatex import PDFLaTeX
from config.app_configs import settings
from .firebase_utils import firebase_upload_file, firebase_download_file_url
import httpx 

def update_resume_for_job_description(content, resume_names, user):
    content = post_process_ai_response(content)

    skills = get_named_section_from_ai_response(content, "SkillsSectionStart", "SkillsSectionEnd")
    experience = get_named_section_from_ai_response(content, "ExperienceSectionStart", "ExperienceSectionEnd")
    projects = get_named_section_from_ai_response(content, "ProjectsSectionStart", "ProjectsSectionEnd")
    
    other_items = []
    split_section_into_section_items(other_items, experience)
    split_section_into_section_items(other_items, projects)

    sections = [skills, other_items]

    return write_to_tex_file_from_job_description(sections, resume_names, user)

def post_process_ai_response(content):
    #remove any occurrences of * or **
    content = content.replace("*", "")

    # replace % with \% for latex
    content = content.replace("%", "\%")
    
    return content.split("\n")

def get_named_section_from_ai_response(content, start, end):
    while len(content) > 0 and start not in content[0]:
        content.pop(0)
    content.pop(0)
    named_section = []
    while len(content) > 0 and end not in content[0]:
        named_section.append(content.pop(0))
    
    return named_section

def split_section_into_section_items(items_array, section):
    remove_heading_now = True
    sub_section = []
    for i in section:
        if not(i == "" or i == " " or i == "\n"):
            if remove_heading_now == True:
                remove_heading_now = False
                continue
            sub_section.append(i)
        else:
            if len(sub_section) > 0:
                items_array.append(sub_section)
            sub_section = []
            remove_heading_now = True
    if len(sub_section) > 0:
        items_array.append(sub_section)    

def append_new_items_to_section_parent(section, new_items):
    for new_item in new_items:
        if new_item == "" or new_item == " " or new_item == "\n":
            continue
        item_tag = TexSoup(f'\\item {new_item}')
        section.parent.append(item_tag)
    

def write_to_tex_file_from_job_description(sections, resume_names, user):
    tex_file_name = resume_names["tex_file_name"]

    resume_tex = download_resume_tex_file_from_firebase(user, tex_file_name)

    if resume_tex.status_code != 200:
        raise Exception("Error downloading tex file") #doesnt work as expected
    
    soup = TexSoup(resume_tex.text)
    
    all_labels = soup.find_all('label')
    skills_section_position = all_labels[0].position
    skills_section_position = soup.char_pos_to_line(skills_section_position)[0]

    for skill in sections[0]:
        if skill == "" or skill == " " or skill == "\n" or len(skill.split(":")) < 2:
            continue
        
        skill_name = skill.split(":")[0]
        skill_values = skill.split(":")[1]
        item_tag = TexSoup(f'\\textbf{{{skill_name}:}} {skill_values} \\\\')
        soup.document.insert(skills_section_position-20, item_tag)
        skills_section_position += 1

    other_section_items = sections[1]
    
    for label in all_labels[1:]:
        append_new_items_to_section_parent(label, other_section_items[all_labels.index(label)-1])
   
    updated_content = str(soup)
    updated_content_lines = updated_content.split("\n")

    for i in range(27):
        updated_content_lines[i] = updated_content_lines[i][2:]

    updated_content = "\n".join(updated_content_lines)

    updated_content = updated_content.encode('utf-8')
    
    return write_to_pdf(updated_content, resume_names, user)
    

def write_to_pdf(content, resume_names, user):
    pdfl = PDFLaTeX.from_binarystring(content, resume_names["output_resume_name"])
    pdfl.set_interaction_mode()
    pdf, log, completed_process = pdfl.create_pdf(keep_pdf_file=False, keep_log_file=False)
    
    output_name = resume_names["output_resume_name"]
    
    return firebase_upload_file(pdf, f'{user.get("user_id")}/{output_name}.pdf', user)
    
def download_resume_tex_file_from_firebase(user, tex_file_name):
    resume_tex_url = firebase_download_file_url(f'{user.get("user_id")}/{tex_file_name}', user)
    return httpx.get(resume_tex_url)

def calculate_input_tex_label_count(input_tex_content):
    string_content = input_tex_content.decode("utf-8")
    soup = TexSoup(string_content)
    labels = soup.find_all('label')
    return len(labels)



