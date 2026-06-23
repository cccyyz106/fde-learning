import os
import json
import base64
import hashlib
import hmac
import time
from datetime import datetime
import shutil
from pathlib import Path
import bcrypt

import chromadb
from docx import Document
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, Depends, Header
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

USERS_FILE = "users.json"
TOKEN_SECRET = os.getenv("TOKEN_SECRET", "dev-secret-change-me")


def load_users():
    if not os.path.exists(USERS_FILE):
        return []

    with open(USERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=2)


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")
    hash_bytes = password_hash.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_token(username: str) -> str:
    payload = {
        "username": username,
        "exp": int(time.time()) + 60 * 60 * 24
    }

    payload_text = json.dumps(payload, ensure_ascii=False)
    payload_base64 = base64.urlsafe_b64encode(payload_text.encode("utf-8")).decode("utf-8")

    signature = hmac.new(
        TOKEN_SECRET.encode("utf-8"),
        payload_base64.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return f"{payload_base64}.{signature}"


def read_token(token: str):
    try:
        payload_base64, signature = token.split(".")

        expected_signature = hmac.new(
            TOKEN_SECRET.encode("utf-8"),
            payload_base64.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=401, detail="登录状态无效。")

        payload_text = base64.urlsafe_b64decode(payload_base64.encode("utf-8")).decode("utf-8")
        payload = json.loads(payload_text)

        if payload["exp"] < int(time.time()):
            raise HTTPException(status_code=401, detail="登录已过期，请重新登录。")

        return payload

    except Exception:
        raise HTTPException(status_code=401, detail="请先登录。")


def get_current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录。")

    token = authorization.replace("Bearer ", "")
    payload = read_token(token)

    users = load_users()
    for user in users:
        if user["username"] == payload["username"]:
            return user

    raise HTTPException(status_code=401, detail="用户不存在。")

app.add_middleware(
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

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "staff"
    department: str = "default"


class LoginRequest(BaseModel):
    username: str
    password: str

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
def upload_doc(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403,
            detail="权限不足，只有管理员或部门负责人可以上传文档。"
        )

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
        "chunk_count": chunk_count,
        "uploaded_by": current_user["username"],
        "role": current_user["role"],
        "department": current_user["department"]
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

@app.post("/register")
def register(request: RegisterRequest):
    username = request.username.strip()
    password = request.password.strip()
    role = request.role.strip()
    department = request.department.strip()

    if username == "" or password == "":
        raise HTTPException(status_code=400, detail="用户名和密码不能为空。")

    users = load_users()

    for user in users:
        if user["username"] == username:
            raise HTTPException(status_code=400, detail="用户名已存在。")

    new_user = {
        "username": username,
        "password_hash": hash_password(password),
        "role": role,
        "department": department,
        "created_at": int(time.time())
    }

    users.append(new_user)
    save_users(users)

    return {
        "message": "注册成功",
        "username": username,
        "role": role,
        "department": department
    }


@app.post("/login")
def login(request: LoginRequest):
    username = request.username.strip()
    password = request.password.strip()

    users = load_users()

    for user in users:
        if user["username"] == username:
            if verify_password(password, user["password_hash"]):
                token = create_token(username)

                return {
                    "message": "登录成功",
                    "token": token,
                    "user": {
                        "username": user["username"],
                        "role": user["role"],
                        "department": user["department"]
                    }
                }

    raise HTTPException(status_code=401, detail="用户名或密码错误。")


@app.get("/me")
def me(current_user=Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "role": current_user["role"],
        "department": current_user["department"]
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