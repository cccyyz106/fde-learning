import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.stdout.reconfigure(encoding="utf-8")


chunks = [
    "员工请年假需要提前 3 个工作日在 OA 系统提交申请，由直属主管审批。",
    "员工报销费用时，需要上传发票、付款截图和报销说明。单笔金额超过 5000 元，需要部门负责人和财务经理共同审批。",
    "新员工入职前三天需要完成账号开通、制度学习、安全培训和直属主管安排的岗位说明。",
    "员工离职需要至少提前 30 天提交离职申请，并完成工作交接、资产归还和系统权限关闭。",
]

question = "报销超过五千块要谁审批？"

vectorizer = TfidfVectorizer(analyzer="char")

all_texts = chunks + [question]

vectors = vectorizer.fit_transform(all_texts)

chunk_vectors = vectors[:-1]
question_vector = vectors[-1]

similarities = cosine_similarity(question_vector, chunk_vectors)[0]

print("用户问题：")
print(question)

print("\n相似度结果：")

for index, score in enumerate(similarities):
    print(f"Chunk {index + 1} 相似度：{score:.4f}")
    print(chunks[index])
    print()

best_index = similarities.argmax()

print("最相关的 chunk：")
print(chunks[best_index])
print("最高相似度：")
print(similarities[best_index])