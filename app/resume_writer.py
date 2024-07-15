from TexSoup import TexSoup
from pdflatex import PDFLaTeX

def update_resume_for_job_description(content):
    content = post_process_ai_response(content)

    skills = get_named_section_from_ai_response(content, "SkillsSectionStart", "SkillsSectionEnd")
    experience = get_named_section_from_ai_response(content, "ExperienceSectionStart", "ExperienceSectionEnd")
    projects = get_named_section_from_ai_response(content, "ProjectsSectionStart", "ProjectsSectionEnd")

    sde = get_named_section_from_ai_response(experience, "sde:", "sdei:")
    sdei = get_named_section_from_ai_response(experience, "sdei:", "ExperienceSectionEnd")

    projects1 = get_named_section_from_ai_response(projects, "projects1:", "projects2:")
    projects2 = get_named_section_from_ai_response(projects, "projects2:", "ProjectsSectionEnd")

    write_to_tex_file_from_job_description(skills, sde, sdei, projects1, projects2)
    return True

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

def write_to_tex_file_from_job_description(skills, sde, sdei, projects1, projects2):
    with open('app/inputFiles/whole_resume.tex', 'r') as file:
        resume_tex = file.read()
    
    soup = TexSoup(resume_tex)
    
    all_labels = soup.find_all('label')

    skills_section_position = all_labels[0].position

    skills_section_position = soup.char_pos_to_line(skills_section_position)[0]

    for skill in skills:
        if skill == "" or skill == " " or skill == "\n":
            continue
        skill_name = skill.split(":")[0]
        skill_values = skill.split(":")[1]
        item_tag = TexSoup(f'\\textbf{{{skill_name}:}} {skill_values} \\\\')
        soup.document.insert(skills_section_position-20, item_tag)
        skills_section_position += 1
    
    for new_item in sde:
        if new_item == "" or new_item == " " or new_item == "\n":
            continue
        item_tag = TexSoup(f'\\item {new_item}')
        all_labels[1].parent.append(item_tag)
    
    for new_item in sdei:
        if new_item == "" or new_item == " " or new_item == "\n":
            continue
        item_tag = TexSoup(f'\\item {new_item}')
        all_labels[2].parent.append(item_tag)
    
    for new_item in projects1:
        if new_item == "" or new_item == " " or new_item == "\n":
            continue
        item_tag = TexSoup(f'\\item {new_item}')
        all_labels[3].parent.append(item_tag)
    
    for new_item in projects2:
        if new_item == "" or new_item == " " or new_item == "\n":
            continue
        item_tag = TexSoup(f'\\item {new_item}')
        all_labels[4].parent.append(item_tag)
    
   
    updated_content = str(soup)

    updated_content_lines = updated_content.split("\n")

    for i in range(27):
        updated_content_lines[i] = updated_content_lines[i][2:]

    updated_content = "\n".join(updated_content_lines)

    with open('app/outputFiles/tex/AIResume.tex', 'w') as file:
        file.write(updated_content)
    
    write_to_pdf()

    return True
    

def write_to_pdf():
    pdfl = PDFLaTeX.from_texfile('app/outputFiles/tex/AIResume.tex')
    pdfl.set_interaction_mode()
    pdf, log, completed_process = pdfl.create_pdf(keep_pdf_file=False, keep_log_file=False)
    
    with open('app/outputFiles/pdf/AIResume.pdf', 'wb') as file:
        file.write(pdf)