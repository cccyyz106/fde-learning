import sys

from docx import Document

sys.stdout.reconfigure(encoding="utf-8")


def read_docx_file(file_path):
    try:
        document = Document(file_path)

        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text != "":
                paragraphs.append(text)

        return "\n".join(paragraphs)

    except FileNotFoundError:
        return "文件不存在，请检查文件路径。"


file_path = "employee_handbook.docx"

document_content = read_docx_file(file_path)

print("读取到的 Word 文档内容：")
print(document_content)

print("文档总字符数：")
print(len(document_content))
