import io
import re
from TexSoup import TexSoup
from pdflatex import PDFLaTeX
from pypdf import PdfReader
from fastapi import HTTPException
from middleware.logging_middleware import logger
from models.ai_models import CoverageReport
from .firebase_utils import firebase_get_tex_file_content

# ---------------------------------------------------------------- latex text

# Escaping happens here and nowhere else: the model is told to return plain
# text, so this is the single point where text becomes LaTeX.
LATEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

def latex_escape(text):
    if text is None:
        return ""
    return "".join(LATEX_ESCAPES.get(character, character) for character in str(text))

def strip_latex(text):
    """Turns stored or model text back into plain text.

    Resumes saved by older clients escaped LaTeX specials before storing them,
    and models occasionally copy an escape sequence through, so both are undone
    before the text is used or re-escaped.
    """
    if not text:
        return ""

    text = text.replace(r"\textbackslash{}", "\\")
    text = text.replace(r"\textasciitilde{}", "~").replace(r"\textasciicircum{}", "^")
    text = re.sub(r"\\([&%$#_{}])", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+\s?", "", text)  # any other stray command
    return re.sub(r"\s+", " ", text).strip()

# ------------------------------------------------------- stored resume text

SECTION_MARKERS = {
    "skills": ("SkillsSectionStart", "SkillsSectionEnd"),
    "experience": ("ExperienceSectionStart", "ExperienceSectionEnd"),
    "projects": ("ProjectsSectionStart", "ProjectsSectionEnd"),
}

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

def _blocks_with_headings(lines):
    """Splits a section into [{heading, bullets}] on blank lines."""
    blocks = []
    current = []

    for line in lines:
        if line.strip() == "":
            if current:
                blocks.append(current)
            current = []
        else:
            current.append(line.strip())

    if current:
        blocks.append(current)

    return [
        {
            # the stored form ends headings with a colon, which is noise in the prompt
            "heading": strip_latex(block[0]).rstrip(":").strip(),
            "bullets": [strip_latex(bullet) for bullet in block[1:]],
        }
        for block in blocks
    ]

def parse_resume_sections(content):
    """Reads the stored resume text into the structure the prompt and the
    template filling both work from."""
    lines = content.split("\n")

    skills_lines = get_named_section_from_ai_response(list(lines), *SECTION_MARKERS["skills"])
    experience_lines = get_named_section_from_ai_response(list(lines), *SECTION_MARKERS["experience"])
    projects_lines = get_named_section_from_ai_response(list(lines), *SECTION_MARKERS["projects"])

    skills = []
    for line in skills_lines:
        if ":" not in line:
            continue
        category, values = line.split(":", 1)
        skills.append({"category": strip_latex(category), "values": strip_latex(values)})

    return {
        "skills": skills,
        "experience": _blocks_with_headings(experience_lines),
        "projects": _blocks_with_headings(projects_lines),
    }

def render_resume_sections_for_prompt(parsed):
    parts = ["Skills:"]
    parts += [f"{group['category']}: {group['values']}" for group in parsed["skills"]]

    for name in ("experience", "projects"):
        if not parsed[name]:
            continue

        parts.append("")
        parts.append(f"{name.capitalize()}:")
        for index, block in enumerate(parsed[name], 1):
            parts.append(f"[{index}] {block['heading']}")
            parts += [f"- {bullet}" for bullet in block["bullets"]]
            parts.append("")

    return "\n".join(parts).strip()

# ------------------------------------------------------------ tex filling

def append_new_items_to_section_parent(section, new_items):
    for new_item in new_items:
        if not new_item or not new_item.strip():
            continue
        item_tag = TexSoup(f'\\item {latex_escape(new_item.strip())}')
        section.parent.append(item_tag)

def write_resume_from_tailored(tailored, resume_names, user):
    """Fills the user's template with the tailored resume and returns the PDF."""
    tex_file_name = resume_names["tex_file_name"]

    resume_tex = firebase_get_tex_file_content(user, tex_file_name)

    if not resume_tex:
        raise HTTPException(
            status_code=400,
            detail="That resume layout is missing its template. Please save your resume again."
        )

    soup = TexSoup(resume_tex)
    all_labels = soup.find_all('label')

    blocks = list(tailored.experience) + list(tailored.projects)

    if len(all_labels) != len(blocks) + 1:
        # the labels in the template and the blocks have to line up one for one,
        # otherwise bullets land under the wrong headings
        raise HTTPException(
            status_code=502,
            detail="The tailored resume did not match your layout. Please try again."
        )

    skills_section_position = all_labels[0].position
    skills_section_position = soup.char_pos_to_line(skills_section_position)[0]

    for group in tailored.skills:
        if not group.category or not group.values:
            continue

        item_tag = TexSoup(f'\\textbf{{{latex_escape(group.category)}:}} {latex_escape(group.values)} \\\\')
        soup.document.insert(skills_section_position-20, item_tag)
        skills_section_position += 1

    for index, label in enumerate(all_labels[1:]):
        append_new_items_to_section_parent(label, blocks[index].bullets)

    updated_content = str(soup)
    updated_content_lines = updated_content.split("\n")

    for i in range(27):
        updated_content_lines[i] = updated_content_lines[i][2:]

    updated_content = "\n".join(updated_content_lines)

    return write_to_pdf(updated_content.encode('utf-8'), resume_names)


def write_to_pdf(content, resume_names):
    pdfl = PDFLaTeX.from_binarystring(content, resume_names["output_resume_name"])
    pdfl.set_interaction_mode()
    pdf, log, completed_process = pdfl.create_pdf(keep_pdf_file=False, keep_log_file=False)

    if not pdf:
        logger.error("pdflatex produced no output: %s", log.decode("utf-8", errors="replace") if isinstance(log, bytes) else log)
        raise HTTPException(
            status_code=500,
            detail="The resume could not be turned into a PDF. Please try again."
        )

    return pdf

# ------------------------------------------------------------ verification

def _normalise_for_search(text):
    return re.sub(r"[^a-z0-9+#. ]", " ", re.sub(r"\s+", " ", text.lower()))

def build_coverage_report(pdf, keywords, skipped):
    """Checks the finished PDF the way an applicant tracking system would: by
    pulling the text back out of it."""
    report = CoverageReport(skipped=skipped or [])

    try:
        reader = PdfReader(io.BytesIO(pdf))
        report.page_count = len(reader.pages)
        text = " ".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        logger.error("could not read back the generated pdf: %s", e)
        report.text_is_extractable = False
        return report

    haystack = _normalise_for_search(text)
    report.text_is_extractable = len(haystack.strip()) > 100

    # a keyword that was deliberately left out already has its own explanation,
    # so it is not repeated as a gap
    explained = {item.keyword.lower() for item in report.skipped}

    for keyword in keywords or []:
        needle = _normalise_for_search(keyword).strip()
        if not needle:
            continue
        if needle in haystack:
            report.covered.append(keyword)
        elif keyword.lower() not in explained:
            report.missing.append(keyword)

    return report

def calculate_input_tex_label_count(input_tex_content):
    string_content = input_tex_content.decode("utf-8")
    soup = TexSoup(string_content)
    labels = soup.find_all('label')
    return len(labels)
