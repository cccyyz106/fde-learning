import os
import json
from datetime import datetime
import shutil
from pathlib import Path

import chromadb
from docx import Document
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

chroma_client = chromadb.PersistentClient(path="../day12/chroma_db")
collection = chroma_client.get_or_create_collection(name="company_docs")

app = FastAPI()

app.add_middlewareapp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("documents")
HISTORY_FILE = Path("history.json")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".txt", ".docx", ".pdf"}


class ChatRequest(BaseModel):
    question: str


class AskDocRequest(BaseModel):
    question: str

class FeedbackRequest(BaseModel):
    created_at: str
    feedback: str


@app.get("/")
def home():
    return {"message": "FDE AI Assistant backend is running."}


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


def load_chunks_from_folders(folder_paths):
    all_chunks = []

    for folder_path in folder_paths:
        folder_path = Path(folder_path)

        if not folder_path.exists():
            continue

        for file_path in folder_path.iterdir():
            if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue

            content = read_document(file_path)
            chunks = split_by_paragraph_then_length(content, chunk_size=100, overlap=15)

            for index, chunk in enumerate(chunks, start=1):
                chunk_data = {
                    "id": f"{file_path.parent.name}-{file_path.stem}-{index}",
                    "file_name": file_path.name,
                    "chunk_index": index,
                    "content": chunk,
                }

                all_chunks.append(chunk_data)

    return all_chunks


def rebuild_chroma():
    global collection

    chunks = load_chunks_from_folders(["../day9", "documents"])

    try:
        chroma_client.delete_collection(name="company_docs")
    except ValueError:
        pass

    collection = chroma_client.get_or_create_collection(name="company_docs")

    if len(chunks) == 0:
        return 0

    texts = [chunk["content"] for chunk in chunks]

    vectorizer = TfidfVectorizer(analyzer="char")
    vectors = vectorizer.fit_transform(texts).toarray()

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

    return len(chunks)


@app.post("/upload-doc")
def upload_doc(file: UploadFile = File(...)):
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="只支持上传 txt、docx、pdf 文件。"
        )

    save_path = UPLOAD_DIR / file.filename

    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    chunk_count = rebuild_chroma()

    return {
        "message": "文件上传成功，知识库已更新",
        "file_name": file.filename,
        "saved_path": str(save_path),
        "chunk_count": chunk_count
    }

@app.get("/documents")
def list_documents():
    files = []

    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            files.append(
                {
                    "file_name": file_path.name,
                    "size": file_path.stat().st_size,
                }
            )

    return {
        "documents": files
    }


@app.delete("/documents/{file_name}")
def delete_document(file_name: str):
    file_path = UPLOAD_DIR / file_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在。")

    file_path.unlink()

    chunk_count = rebuild_chroma()

    return {
        "message": "文件删除成功，知识库已更新",
        "file_name": file_name,
        "chunk_count": chunk_count
    }


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question.strip()

    if question == "":
        raise HTTPException(status_code=400, detail="问题不能为空。")

    if not os.getenv("DEEPSEEK_API_KEY"):
        raise HTTPException(status_code=500, detail="缺少 DEEPSEEK_API_KEY，请检查 .env 文件。")

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个企业知识库 AI 助手，同时具备 FDE 项目助理能力。"
                    "回答时请使用简洁、准确的中文。"
                    "如果用户的问题涉及企业制度、流程、知识库、RAG、API 或后端项目，"
                    "请优先从企业 AI 落地和实际业务价值角度解释。"
                    "如果用户问题太模糊，请先指出可能存在多种含义，并给出最可能的解释。"
                )
            },
            {
                "role": "user",
                "content": question
            }
        ],
        stream=False
    )

    ai_answer = response.choices[0].message.content

    return {
        "question": question,
        "answer": ai_answer,
        "provider": "DeepSeek",
        "model": "deepseek-v4-flash"
    }


def search_chroma(question, top_k):
    data = collection.get(include=["documents", "metadatas", "embeddings"])

    documents = data["documents"]
    metadatas = data["metadatas"]

    if len(documents) == 0:
        raise HTTPException(status_code=500, detail="Chroma 知识库为空，请先上传文档。")

    vectorizer = TfidfVectorizer(analyzer="char")

    all_texts = documents + [question]

    vectors = vectorizer.fit_transform(all_texts)

    chunk_vectors = vectors[:-1]
    question_vector = vectors[-1]

    similarities = cosine_similarity(question_vector, chunk_vectors)[0]

    results = []

    for index, score in enumerate(similarities):
        result = {
            "score": float(score),
            "file_name": metadatas[index]["file_name"],
            "chunk_index": metadatas[index]["chunk_index"],
            "content": documents[index],
        }

        results.append(result)

    results = sorted(results, key=lambda item: item["score"], reverse=True)

    return results[:top_k]


def build_context(search_results):
    context_parts = []

    for index, result in enumerate(search_results, start=1):
        context = (
            f"资料 {index}\n"
            f"文件名：{result['file_name']}\n"
            f"Chunk 编号：{result['chunk_index']}\n"
            f"内容：{result['content']}"
        )

        context_parts.append(context)

    return "\n\n".join(context_parts)


def ask_ai_with_context(question, context):
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {
                "role": "system",
                "content": (
                   "你是一个企业知识库 AI 助手。"
"你必须优先根据提供的资料回答问题。"
"回答时请先给出直接答案，再用一句话说明依据来自哪份资料。"
"如果多段资料都出现时间，请判断哪一段最符合用户问题，不要只看相似度。"
"如果资料之间有冲突，请说明无法确认，并建议联系负责人。"
"如果资料中没有明确答案，请说：根据当前知识库资料，无法确认。"
"不要编造企业制度。"
"回答要简洁、准确，使用中文。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"请根据下面的企业资料回答问题。\n\n"
                    f"企业资料：\n{context}\n\n"
                    f"用户问题：{question}"
                )
            }
        ],
        stream=False
    )

    return response.choices[0].message.content

def load_history():
    if not HISTORY_FILE.exists():
        return []

    with open(HISTORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_history_item(question, answer, sources):
    history = load_history()

    item = {
    "question": question,
    "answer": answer,
    "sources": sources,
    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "feedback": ""
}

    history.insert(0, item)

    history = history[:50]

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)
@app.post("/ask-doc")
def ask_doc(request: AskDocRequest):
    question = request.question.strip()

    if question == "":
        raise HTTPException(status_code=400, detail="问题不能为空。")

    if not os.getenv("DEEPSEEK_API_KEY"):
        raise HTTPException(status_code=500, detail="缺少 DEEPSEEK_API_KEY，请检查 .env 文件。")

    search_results = search_chroma(question, top_k=5)



    reliable_sources = search_results

    context = build_context(reliable_sources)

    answer = ask_ai_with_context(question, context)
    save_history_item(question, answer, reliable_sources)

    return {
        "question": question,
        "answer": answer,
        "sources": reliable_sources,
        "provider": "DeepSeek",
        "model": "deepseek-v4-flash"
    }

@app.get("/history")
def get_history():
    return {
        "history": load_history()
    }
@app.post("/feedback")
def save_feedback(request: FeedbackRequest):
    history = load_history()

    if request.feedback not in ["useful", "not_useful"]:
        raise HTTPException(status_code=400, detail="feedback 只能是 useful 或 not_useful。")

    for item in history:
        if item["created_at"] == request.created_at:
            item["feedback"] = request.feedback

            with open(HISTORY_FILE, "w", encoding="utf-8") as file:
                json.dump(history, file, ensure_ascii=False, indent=2)

            return {
                "message": "反馈已保存",
                "created_at": request.created_at,
                "feedback": request.feedback
            }

    raise HTTPException(status_code=404, detail="没有找到对应的历史记录。")