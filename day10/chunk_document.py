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

    return ""


def split_with_overlap(text, chunk_size, overlap):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk != "":
            chunks.append(chunk)

        start = start + chunk_size - overlap

    return chunks


file_path = "../day9/company_policy.txt"

content = read_document(file_path)

chunks = split_with_overlap(content, chunk_size=60, overlap=10)

print("读取的文件：")
print(file_path)

print("\n文档总字符数：")
print(len(content))

print("\n切分后的 chunk 数量：")
print(len(chunks))

for index, chunk in enumerate(chunks, start=1):
    print("\n--------------------")
    print(f"Chunk {index}")
    print(f"字符数：{len(chunk)}")
    print(chunk)