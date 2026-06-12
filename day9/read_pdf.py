import sys

from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8")


def read_pdf_file(file_path):
    reader = PdfReader(file_path)

    pages_text = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages_text.append(text.strip())

    return "\n".join(pages_text)


file_path = "company_faq.pdf"

content = read_pdf_file(file_path)

print("读取到的 PDF 内容：")
print(content)

print("文档总字符数：")
print(len(content))