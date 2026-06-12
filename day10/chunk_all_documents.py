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


documents_folder = Path("../day9")

supported_files = []

for file_path in documents_folder.iterdir():
    if file_path.suffix in [".txt", ".docx", ".pdf"]:
        supported_files.append(file_path)

print("找到的文档：")

for file_path in supported_files:
    print("-", file_path.name)

print("\n开始读取并切分：")

all_chunks = []

for file_path in supported_files:
    content = read_document(file_path)

    chunks = split_with_overlap(content, chunk_size=60, overlap=10)

    for index, chunk in enumerate(chunks, start=1):
        chunk_data = {
            "file_name": file_path.name,
            "chunk_index": index,
            "content": chunk,
            "char_count": len(chunk),
        }

        all_chunks.append(chunk_data)

print("\n总 chunk 数量：")
print(len(all_chunks))

for chunk in all_chunks:
    print("\n--------------------")
    print(f"文件名：{chunk['file_name']}")
    print(f"Chunk 编号：{chunk['chunk_index']}")
    print(f"字符数：{chunk['char_count']}")
    print(chunk["content"])