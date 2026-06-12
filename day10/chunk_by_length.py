import sys

sys.stdout.reconfigure(encoding="utf-8")


text = """
员工请年假需要提前 3 个工作日在 OA 系统提交申请，由直属主管审批。

员工报销费用时，需要上传发票、付款截图和报销说明。单笔金额超过 5000 元，需要部门负责人和财务经理共同审批。

新员工入职前三天需要完成账号开通、制度学习、安全培训和直属主管安排的岗位说明。

员工离职需要至少提前 30 天提交离职申请，并完成工作交接、资产归还和系统权限关闭。
"""


def split_by_length(text, chunk_size):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk != "":
            chunks.append(chunk)

        start = end

    return chunks


chunks = split_by_length(text, 50)

print("切分后的 chunk 数量：")
print(len(chunks))

for index, chunk in enumerate(chunks, start=1):
    print("\n--------------------")
    print(f"Chunk {index}")
    print(f"字符数：{len(chunk)}")
    print(chunk)