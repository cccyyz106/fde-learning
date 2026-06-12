import sys

from docx import Document
from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8")


def read_txt_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def read_docx_file(file_path):
    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text != "":
            paragraphs.append(text)

    return "\n".join(paragraphs)


def read_pdf_file(file_path):
    reader = PdfReader(file_path)

    pages_text = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages_text.append(text.strip())

    return "\n".join(pages_text)


def read_document(file_path):
    if file_path.endswith(".txt"):
        return read_txt_file(file_path)

    if file_path.endswith(".docx"):
        return read_docx_file(file_path)

    if file_path.endswith(".pdf"):
        return read_pdf_file(file_path)

    return "暂不支持这个文件类型。"


file_path = "company_faq.pdf"

content = read_document(file_path)

print("读取结果：")
print(content)

print("文档总字符数：")
print(len(content))