import sys

import chromadb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.stdout.reconfigure(encoding="utf-8")


client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="company_docs")

data = collection.get(include=["documents", "metadatas", "embeddings"])

documents = data["documents"]
metadatas = data["metadatas"]
embeddings = data["embeddings"]

question = input("请输入你的问题：")

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

top_results = results[:3]

print("\n最相关的 3 个 chunk：")

for result in top_results:
    print("\n--------------------")
    print(f"相似度：{result['score']:.4f}")
    print(f"文件名：{result['file_name']}")
    print(f"Chunk 编号：{result['chunk_index']}")
    print(result["content"])