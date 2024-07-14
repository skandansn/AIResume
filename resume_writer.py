from TexSoup import TexSoup
from pdflatex import PDFLaTeX

def fix_percentage_sign(content):
    content = content.replace("%", "\%")
    return content

def seperate_labels_from_ai_response(content):
    content = fix_percentage_sign(content)
    sde = []
    sdei = []
    content = content.split("\n")
    while len(content) > 0 and "sde:" not in content[0]:
        content.pop(0)
    content.pop(0)
    while len(content) > 0 and "sdei:" not in content[0] :
        sde.append(content.pop(0))
    content.pop(0)
    while len(content) > 0:
        sdei.append(content.pop(0))

    return sde, sdei

def update_resume(content):
    sde, sdei = seperate_labels_from_ai_response(content)
    # print(sde)
    # print(sdei)
    write_to_tex_file(sde, sdei)
    return True



def write_to_tex_file(sde, sdei):
# load the tex file
    with open('./input/main.tex', 'r') as file:
        resume_tex = file.read()

    # parse the tex file
    soup = TexSoup(resume_tex)

    all_labels = soup.find_all('label')
    parent_all_labels = []
    for label in all_labels:
        parent_all_labels.append(label.parent)


    for new_item in sde:
        if new_item == "" or new_item == " " or new_item == "\n":
            continue
        item_tag = TexSoup(f'\\item {new_item}')
        parent_all_labels[0].append(item_tag)

    for new_item in sdei:
        if new_item == "" or new_item == " " or new_item == "\n":
            continue
        item_tag = TexSoup(f'\\item {new_item}')
        parent_all_labels[1].append(item_tag)
    
    updated_content = str(soup)

    updated_content_lines = updated_content.split("\n")

    for i in range(27):
        updated_content_lines[i] = updated_content_lines[i][2:]
    
    updated_content = "\n".join(updated_content_lines)
    
    # save the updated tex file
    with open('./output/main_updated.tex', 'w') as file:
        file.write(updated_content)
    
    print("Resume updated successfully!")

    write_to_pdf()

    return True

def write_to_pdf():
    pdfl = PDFLaTeX.from_texfile('./output/main_updated.tex')
    pdfl.set_interaction_mode()
    pdf, log, completed_process = pdfl.create_pdf(keep_pdf_file=True, keep_log_file=True)
    