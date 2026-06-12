def read_txt_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            return content
    except FileNotFoundError:
        return "文件不存在，请检查文件路径。"


file_path = "company_policy.txt"

document_content = read_txt_file(file_path)

print("读取到的文档内容：")
print(document_content)

print("文档总字符数：")
print(len(document_content))

paragraphs = document_content.split("\n\n")

print("文档段落数：")
print(len(paragraphs))

print("第一段内容：")
print(paragraphs[0])