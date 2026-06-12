import sys
from pathlib import Path

from docx import Document
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
                "file_name": file_path.name,
                "chunk_index": index,
                "content": chunk,
            }

            all_chunks.append(chunk_data)

    return all_chunks


def search_top_chunks(question, chunks, top_k):
    texts = [chunk["content"] for chunk in chunks]

    vectorizer = TfidfVectorizer(analyzer="char")

    all_texts = texts + [question]

    vectors = vectorizer.fit_transform(all_texts)

    chunk_vectors = vectors[:-1]
    question_vector = vectors[-1]

    similarities = cosine_similarity(question_vector, chunk_vectors)[0]

    results = []

    for index, score in enumerate(similarities):
        result = {
            "score": score,
            "file_name": chunks[index]["file_name"],
            "chunk_index": chunks[index]["chunk_index"],
            "content": chunks[index]["content"],
        }

        results.append(result)

    results = sorted(results, key=lambda item: item["score"], reverse=True)

    return results[:top_k]


chunks = load_chunks_from_folder("../day9")

question = input("请输入你的问题：")

results = search_top_chunks(question, chunks, top_k=3)

print("用户问题：")
print(question)

print("\n最相关的 chunk：")

for result in results:
    print("\n--------------------")
    print(f"相似度：{result['score']:.4f}")
    print(f"文件名：{result['file_name']}")
    print(f"Chunk 编号：{result['chunk_index']}")
    print(result["content"])