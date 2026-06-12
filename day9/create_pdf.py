from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

pdfmetrics.registerFont(TTFont("SimSun", "C:/Windows/Fonts/simsun.ttc"))

pdf = canvas.Canvas("company_faq.pdf")
pdf.setFont("SimSun", 12)

lines = [
    "员工请年假需要提前 3 个工作日在 OA 系统提交申请。",
    "员工报销费用时，需要上传发票、付款截图和报销说明。",
    "新员工入职前三天需要完成账号开通、制度学习和安全培训。",
]

y = 800

for line in lines:
    pdf.drawString(50, y, line)
    y -= 30

pdf.save()

print("PDF 文件创建成功。")