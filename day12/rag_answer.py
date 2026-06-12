import os
import sys

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv("../day4/.env")

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")

collection = chroma_client.get_or_create_collection(name="company_docs")


def search_chroma(question, top_k):
    data = collection.get(include=["documents", "metadatas", "embeddings"])

    documents = data["documents"]
    metadatas = data["metadatas"]

    vectorizer = TfidfVectorizer(analyzer="char")

    all_texts = documents + [question]

    vectors = vectorizer.fit_transform(all_texts)

    chunk_vectors = vectors[:-1]
    question_vector = vectors[-1]

    similarities = cosine_similarity(question_vector, chunk_vectors)[0]

    results = []

    for index, score in enumerate(similarities):
        result = {
            "score": score,
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


def ask_ai(question, context):
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个企业知识库 AI 助手。"
                    "你必须优先根据提供的资料回答问题。"
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


question = input("请输入你的问题：")

search_results = search_chroma(question, top_k=3)

context = build_context(search_results)

answer = ask_ai(question, context)

print("\nAI 回答：")
print(answer)

print("\n引用来源：")

for result in search_results:
    print("\n--------------------")
    print(f"相似度：{result['score']:.4f}")
    print(f"文件名：{result['file_name']}")
    print(f"Chunk 编号：{result['chunk_index']}")
    print(result["content"])