"use client";

import { useEffect, useRef, useState } from "react";

const API_BASE_URL = "http://47.108.136.208:8000";

type Source = {
  file_name?: string;
  content?: string;
  score?: number;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  hiddenSourceCount?: number;
};

type DocumentItem = {
  file_name: string;
  size?: number;
};
type HistoryItem = {
  question: string;
  answer: string;
  created_at: string;
  feedback?: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "你好，我是企业知识库 AI 助手。你可以问我企业制度、流程、文档内容相关的问题。",
    },
  ]);

  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorText, setErrorText] = useState("");
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
  loadDocuments();
  loadHistory();
}, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function loadDocuments() {
    try {
      const response = await fetch(`${API_BASE_URL}/documents`);
      if (!response.ok) {
        throw new Error("获取文档列表失败");
      }

      const data = await response.json();
      setDocuments(data.documents || []);
    } catch {
      setDocuments([]);
    }
  }
  async function loadHistory() {
  try {
    const response = await fetch(`${API_BASE_URL}/history`);

    if (!response.ok) {
      throw new Error("获取历史记录失败");
    }

    const data = await response.json();
    setHistory(data.history || []);
  } catch {
    setHistory([]);
  }
}
async function submitFeedback(createdAt: string, feedback: "useful" | "not_useful") {
  try {
    const response = await fetch(`${API_BASE_URL}/feedback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        created_at: createdAt,
        feedback,
      }),
    });

    if (!response.ok) {
      throw new Error("提交反馈失败");
    }

    await loadHistory();
  } catch {
    setErrorText("反馈提交失败，请检查后端是否正常运行。");
  }
}
  async function sendMessage() {
    const text = question.trim();

    if (!text || loading) return;

    setErrorText("");
    setQuestion("");

    const userMessage: Message = {
      role: "user",
      content: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/ask-doc`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: text,
        }),
      });

      if (!response.ok) {
        throw new Error(`请求失败，状态码：${response.status}`);
      }

      const data = await response.json();

      const sources: Source[] = Array.isArray(data.sources) ? data.sources : [];
const highScoreSources = sources.filter((item) => {
  const score = Number(item.score ?? 0);
  return score > 0.3;
});

const displaySources = highScoreSources;

const assistantMessage: Message = {
  role: "assistant",
  content: data.answer || "我没有拿到有效回答。",
  sources: displaySources,
  hiddenSourceCount: sources.length - displaySources.length,
};

      setMessages((prev) => [...prev, assistantMessage]);
      loadHistory();
    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content:
          "后端暂时没有成功返回结果。请检查 FastAPI 是否已经启动，或者文档库是否已经建立。",
      };

      setMessages((prev) => [...prev, errorMessage]);
      setErrorText(error instanceof Error ? error.message : "未知错误");
    } finally {
      setLoading(false);
    }
  }

  async function uploadDocument() {
    if (!selectedFile || uploading) return;

    setUploading(true);
    setErrorText("");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(`${API_BASE_URL}/upload-doc`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`上传失败，状态码：${response.status}`);
      }

      setSelectedFile(null);
      await loadDocuments();
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "上传失败");
    } finally {
      setUploading(false);
    }
  }

  async function deleteDocument(fileName: string) {
    const ok = window.confirm(`确定删除 ${fileName} 吗？`);
    if (!ok) return;

    setErrorText("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/documents/${encodeURIComponent(fileName)}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error(`删除失败，状态码：${response.status}`);
      }

      await loadDocuments();
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "删除失败");
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <main className="min-h-screen bg-[#f5f5f7] text-[#1d1d1f]">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 py-6 sm:px-6">
        <header className="mb-5 flex items-center justify-between rounded-[28px] border border-white/70 bg-white/75 px-5 py-4 shadow-[0_18px_60px_rgba(0,0,0,0.08)] backdrop-blur-xl">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-[#6e6e73]">
              Enterprise RAG Assistant
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight">
              企业知识库 AI 助手
            </h1>
          </div>

          <div className="hidden rounded-full bg-[#e8f3ff] px-4 py-2 text-sm font-medium text-[#0066cc] sm:block">
            Demo 版本
          </div>
        </header>

        <section className="flex flex-1 flex-col overflow-hidden rounded-[32px] border border-white/80 bg-white/80 shadow-[0_24px_80px_rgba(0,0,0,0.10)] backdrop-blur-xl">
          <div className="flex-1 space-y-5 overflow-y-auto px-4 py-6 sm:px-7">
            {messages.map((message, index) => {
              const isUser = message.role === "user";

              return (
                <div
                  key={index}
                  className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[86%] rounded-[26px] px-5 py-4 text-[15px] leading-7 shadow-sm sm:max-w-[74%] ${
                      isUser
                        ? "bg-[#0071e3] text-white"
                        : "border border-[#e5e5ea] bg-white text-[#1d1d1f]"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>

                    {!isUser && message.sources && message.sources.length > 0 && (
                      <details className="mt-4 rounded-2xl border border-[#e5e5ea] bg-[#f5f5f7] px-4 py-3">
                        <summary className="cursor-pointer text-xs font-medium text-[#6e6e73]">
                          参考来源 {message.sources.length} 条
                        </summary>

                        <div className="mt-3 space-y-3">
                          {message.sources.map((source, sourceIndex) => (
                            <div
                              key={sourceIndex}
                              className="rounded-xl bg-white px-3 py-3 text-xs leading-5 text-[#515154]"
                            >
                              <div className="mb-1 flex flex-wrap items-center gap-2 text-[11px] font-medium text-[#86868b]">
                                <span>{source.file_name || "未知文档"}</span>
                                {typeof source.score === "number" && (
                                  <span>
                                    相似度：{source.score.toFixed(2)}
                                  </span>
                                )}
                              </div>
                              <p className="line-clamp-4">
                                {source.content || "没有来源内容"}
                              </p>
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                    {!isUser &&
  message.sources &&
  message.sources.length === 0 &&
  (message.hiddenSourceCount ?? 0) > 0 && (
    <p className="mt-3 rounded-2xl bg-[#f5f5f7] px-4 py-3 text-xs text-[#86868b]">
      本次未展示高相似度来源，回答仅供参考。
    </p>
  )}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-[26px] border border-[#e5e5ea] bg-white px-5 py-4 text-sm text-[#6e6e73] shadow-sm">
                  正在检索文档并生成回答...
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {errorText && (
            <div className="mx-4 mb-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600 sm:mx-7">
              {errorText}
            </div>
          )}

          <div className="border-t border-[#e5e5ea] bg-white/85 px-4 py-4 backdrop-blur-xl sm:px-7">
            <div className="flex gap-3">
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入你的问题，例如：员工请假流程是什么？"
                className="min-h-[52px] flex-1 resize-none rounded-[22px] border border-[#d2d2d7] bg-[#f5f5f7] px-4 py-3 text-[15px] leading-6 outline-none transition focus:border-[#0071e3] focus:bg-white focus:ring-4 focus:ring-[#0071e3]/10"
              />

              <button
                onClick={sendMessage}
                disabled={loading || question.trim() === ""}
                className="h-[52px] rounded-[22px] bg-[#0071e3] px-6 text-sm font-semibold text-white transition hover:bg-[#0077ed] disabled:cursor-not-allowed disabled:bg-[#c7c7cc]"
              >
                {loading ? "思考中" : "发送"}
              </button>
            </div>
          </div>
        </section>

        <details className="mt-5 rounded-[28px] border border-white/80 bg-white/70 px-5 py-4 shadow-[0_18px_60px_rgba(0,0,0,0.06)] backdrop-blur-xl">
          <summary className="cursor-pointer text-sm font-semibold text-[#1d1d1f]">
            管理员文档管理
          </summary>

          <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_1.2fr]">
            <div className="rounded-[22px] border border-[#e5e5ea] bg-white p-4">
              <p className="mb-3 text-sm font-medium text-[#1d1d1f]">
                上传企业文档
              </p>

              <input
                type="file"
                accept=".txt,.docx,.pdf"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  setSelectedFile(file || null);
                }}
                className="block w-full text-sm text-[#6e6e73] file:mr-4 file:rounded-full file:border-0 file:bg-[#f5f5f7] file:px-4 file:py-2 file:text-sm file:font-medium file:text-[#1d1d1f]"
              />

              <button
                onClick={uploadDocument}
                disabled={!selectedFile || uploading}
                className="mt-4 w-full rounded-full bg-[#1d1d1f] px-4 py-3 text-sm font-semibold text-white transition hover:bg-black disabled:cursor-not-allowed disabled:bg-[#c7c7cc]"
              >
                {uploading ? "上传中..." : "上传并更新知识库"}
              </button>
            </div>

            <div className="rounded-[22px] border border-[#e5e5ea] bg-white p-4">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm font-medium text-[#1d1d1f]">
                  已上传文档
                </p>

                <button
                  onClick={loadDocuments}
                  className="rounded-full bg-[#f5f5f7] px-3 py-1.5 text-xs font-medium text-[#515154] transition hover:bg-[#e5e5ea]"
                >
                  刷新
                </button>
              </div>

              {documents.length === 0 ? (
                <p className="rounded-2xl bg-[#f5f5f7] px-4 py-4 text-sm text-[#86868b]">
                  当前还没有上传的文档。
                </p>
              ) : (
                <div className="space-y-2">
                  {documents.map((doc) => (
                    <div
                      key={doc.file_name}
                      className="flex items-center justify-between gap-3 rounded-2xl bg-[#f5f5f7] px-4 py-3"
                    >
                      <span className="truncate text-sm text-[#1d1d1f]">
                        {doc.file_name}
                      </span>

                      <button
                        onClick={() => deleteDocument(doc.file_name)}
                        className="shrink-0 rounded-full bg-white px-3 py-1.5 text-xs font-medium text-red-500 transition hover:bg-red-50"
                      >
                        删除
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </details>
        <details className="mt-4 rounded-[28px] border border-white/80 bg-white/70 px-5 py-4 shadow-[0_18px_60px_rgba(0,0,0,0.06)] backdrop-blur-xl">
  <summary className="cursor-pointer text-sm font-semibold text-[#1d1d1f]">
    最近提问记录
  </summary>

  <div className="mt-4 space-y-3">
    {history.length === 0 ? (
      <p className="rounded-2xl bg-[#f5f5f7] px-4 py-4 text-sm text-[#86868b]">
        暂时还没有历史记录。
      </p>
    ) : (
      history.slice(0, 8).map((item, index) => (
        <div
          key={index}
          className="rounded-2xl border border-[#e5e5ea] bg-white px-4 py-3"
        >
          <div className="mb-2 flex items-center justify-between gap-3">
            <p className="truncate text-sm font-medium text-[#1d1d1f]">
              {item.question}
            </p>
            <span className="shrink-0 text-xs text-[#86868b]">
              {item.created_at}
            </span>
          </div>

          <p className="line-clamp-2 text-xs leading-5 text-[#6e6e73]">
            {item.answer}
          </p>
          <div className="mt-3 flex items-center gap-2">
  <button
    onClick={() => submitFeedback(item.created_at, "useful")}
    className={`rounded-full px-3 py-1 text-xs font-medium transition ${
      item.feedback === "useful"
        ? "bg-[#0071e3] text-white"
        : "bg-[#f5f5f7] text-[#515154] hover:bg-[#e5e5ea]"
    }`}
  >
    有用
  </button>

  <button
    onClick={() => submitFeedback(item.created_at, "not_useful")}
    className={`rounded-full px-3 py-1 text-xs font-medium transition ${
      item.feedback === "not_useful"
        ? "bg-red-500 text-white"
        : "bg-[#f5f5f7] text-[#515154] hover:bg-[#e5e5ea]"
    }`}
  >
    没用
  </button>
</div>
        </div>
      ))
    )}
  </div>
</details>
      </div>
    </main>
  );
}
