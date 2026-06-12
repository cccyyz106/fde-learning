import sys
from pathlib import Path

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
    file_path = Path(file_path)

    if file_path.suffix == ".txt":
        return read_txt_file(file_path)

    if file_path.suffix == ".docx":
        return read_docx_file(file_path)

    if file_path.suffix == ".pdf":
        return read_pdf_file(file_path)

    return None


folder_path = Path(".")

supported_files = []

for file_path in folder_path.iterdir():
    if file_path.suffix in [".txt", ".docx", ".pdf"]:
        supported_files.append(file_path)

print("找到的可读取文档：")

for file_path in supported_files:
    print("-", file_path.name)

print("\n开始读取文档内容：")

for file_path in supported_files:
    content = read_document(file_path)

    print("\n==============================")
    print(f"文件名：{file_path.name}")
    print(f"字符数：{len(content)}")
    print("内容：")
    print(content)