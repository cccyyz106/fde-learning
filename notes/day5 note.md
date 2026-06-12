Day 5：调用大模型 API
1. 今天学会了什么？
今天我学习了 API Key、.env 文件、环境变量和大模型 API 调用。

API Key 可以理解成调用大模型服务的钥匙，用来证明我有权限使用这个 AI 服务，并且调用费用会算到我的账号上。

.env 文件用来保存 API Key 这种敏感信息，避免直接写进代码里。这样以后代码上传到 GitHub 时，不容易泄露密钥。

今天还学习了 system message 和 user message：

system message：用来设定 AI 的身份、规则和回答风格。
user message：用户真正提出的问题。
2. 今天做出了什么？
今天我把 /chat 接口从固定回答升级成了真实 AI 回答。

昨天的 /chat 是：

用户提交 question
后端返回固定的 answer
今天的 /chat 是：

用户提交 question
FastAPI 后端读取 .env 里的 DEEPSEEK_API_KEY
后端调用 DeepSeek 大模型
DeepSeek 生成回答
后端把 AI 回答返回给 Apifox
现在接口返回内容包括：

question：用户的问题
answer：AI 生成的回答
provider：模型服务商，例如 DeepSeek
model：使用的模型名称
3. 今天最卡的地方是什么？
今天最卡的地方是 Apifox 一开始返回了 500 错误。

后来我理解了：500 表示后端内部出错，不是 Apifox 的问题。
这次主要原因是后端没有正确读取到 API Key。

解决方式是：

检查 .env 文件是否存在
确认变量名是 DEEPSEEK_API_KEY
保存 .env 和 main.py
用 Ctrl + C 停掉后端服务
重新运行 python -m uvicorn main:app --reload
4. 今天的加练做了什么？
今天给 /chat 接口加了三个优化。

第一，空问题返回 400。

如果用户提交空问题，后端不会再调用 AI，而是返回：

状态码：400
提示：问题不能为空。
第二，使用了 strip()。

strip() 可以去掉用户问题前后的空格。
如果用户只输入空格，处理后就会变成空字符串，然后返回 400。

第三，返回了 provider 和 model。

这样可以清楚知道这次回答来自哪个模型服务，方便后续调试、日志记录和项目展示。

5. 今天学到的重要概念
API Key：调用大模型服务的钥匙。

.env：保存密钥和配置的文件。

python-dotenv：读取 .env 文件的工具。

openai：调用 OpenAI 兼容格式大模型 API 的 Python 工具包。

base_url：指定请求发到哪个大模型服务商。

system message：设定 AI 身份和规则。

user message：用户真正提出的问题。

HTTPException：FastAPI 里用来返回错误状态码的工具。

400：用户请求数据有问题。

500：后端服务器内部出错。

6. 今天完整链路
今天完成的链路是：

Apifox 提交问题
↓
FastAPI /chat 接收 question
↓
后端检查问题是否为空
↓
后端读取 .env 里的 DEEPSEEK_API_KEY
↓
后端调用 DeepSeek API
↓
DeepSeek 生成 AI 回答
↓
FastAPI 返回 JSON
↓
Apifox 显示 answer

7. 如果给客户讲，我会怎么说？
如果给客户讲，我会说：

今天我完成了企业知识库 AI 助手的 AI 问答后端。用户可以向 /chat 接口提交问题，后端会调用 DeepSeek 大模型生成回答，并把结果返回给用户。

同时，为了安全，我没有把 API Key 写死在代码里，而是放在 .env 文件中。这样后续上传 GitHub 或部署项目时，可以降低密钥泄露风险。

我还加入了基础错误处理。如果用户提交空问题，系统会返回 400，提示问题不能为空。这样接口更接近真实企业项目里的后端设计。

8. 今天的面试表达
我完成了一个可以调用大模型的 AI 问答后端。后端使用 FastAPI 实现 /chat 接口，通过 .env 读取 DeepSeek API Key，并使用 OpenAI 兼容 SDK 调用 DeepSeek 模型。

用户通过 POST 请求提交 question 后，后端会先校验问题是否为空，再把问题发送给大模型，最后将 AI 生成的 answer 以 JSON 格式返回。

这个接口是企业知识库 AI 助手的基础后端能力，后续可以继续接入文档上传、文本切分、向量检索和 RAG，让 AI 基于企业内部资料回答问题。

9. 明天要解决什么？
明天要学习 Git 和 GitHub，把第一周的小项目整理成一个可以展示的代码仓库。

明天重点包括：

整理项目结构
创建 requirements.txt
创建 .gitignore
写 README.md
初始化 Git 仓库
提交代码
准备上传 GitHub