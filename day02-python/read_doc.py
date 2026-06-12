def read_text_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return ""


def analyze_document(file_path, content):
    print("文档名称：", file_path)
    print("文档字数：", len(content))
    print("文档预览：")
    print(content[:100])

    print("简单总结：")
    if "考勤" in content:
        print("这是一份关于公司考勤制度的文档。")
    elif "请假" in content:
        print("这是一份关于请假流程的企业文档。")
    else:
        print("这是一份企业内部文档。")


file_path = "company_policy.txt"
content = read_text_file(file_path)

if content == "":
    print("文件读取失败，请检查文件是否存在。")
else:
    analyze_document(file_path, content)