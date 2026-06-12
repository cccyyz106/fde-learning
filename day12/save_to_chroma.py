import sys
from pathlib import Path

import chromadb
from docx import Document
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer

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

    return "\n\n".join(paragraphs)


def read_pdf_file(file_path):
    reader = PdfReader(file_path)

    pages_text = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages_text.append(text.strip())

    return "\n\n".join(pages_text)


def read_document(file_path):
    file_path = Path(file_path)

    if file_path.suffix == ".txt":
        return read_txt_file(file_path)

    if file_path.suffix == ".docx":
        return read_docx_file(file_path)

    if file_path.suffix == ".pdf":
        return read_pdf_file(file_path)

    return ""


def split_by_length(text, chunk_size, overlap):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk != "":
            chunks.append(chunk)

        start = start + chunk_size - overlap

    return chunks


def split_by_paragraph_then_length(text, chunk_size, overlap):
    paragraphs = text.split("\n\n")

    chunks = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if paragraph == "":
            continue

        if len(paragraph) <= chunk_size:
            chunks.append(paragraph)
        else:
            sub_chunks = split_by_length(paragraph, chunk_size, overlap)
            chunks.extend(sub_chunks)

    return chunks


def load_chunks_from_folder(folder_path):
    folder_path = Path(folder_path)

    all_chunks = []

    for file_path in folder_path.iterdir():
        if file_path.suffix not in [".txt", ".docx", ".pdf"]:
            continue

        content = read_document(file_path)

        chunks = split_by_paragraph_then_length(content, chunk_size=100, overlap=15)

        for index, chunk in enumerate(chunks, start=1):
            chunk_data = {
                "id": f"{file_path.stem}-{index}",
                "file_name": file_path.name,
                "chunk_index": index,
                "content": chunk,
            }

            all_chunks.append(chunk_data)

    return all_chunks


chunks = load_chunks_from_folder("../day9")

texts = [chunk["content"] for chunk in chunks]

vectorizer = TfidfVectorizer(analyzer="char")

vectors = vectorizer.fit_transform(texts).toarray()

client = chromadb.PersistentClient(path="./chroma_db")

try:
    client.delete_collection(name="company_docs")
except ValueError:
    pass

collection = client.get_or_create_collection(name="company_docs")
collection.add(
    ids=[chunk["id"] for chunk in chunks],
    documents=[chunk["content"] for chunk in chunks],
    embeddings=vectors.tolist(),
    metadatas=[
        {
            "file_name": chunk["file_name"],
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in chunks
    ],
)

print("已写入 Chroma 的 chunk 数量：")
print(len(chunks))

print("\n数据库路径：")
print("./chroma_db")