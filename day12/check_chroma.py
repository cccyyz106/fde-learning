import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="company_docs")

count = collection.count()

print("Chroma 当前保存的 chunk 数量：")
print(count)