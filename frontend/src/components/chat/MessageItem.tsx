import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../../lib/chat";

/** 单条消息：用户消息保留换行原样展示，助手消息按 Markdown 渲染（含表格/任务列表）。 */
export default function MessageItem({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-2 text-xs font-medium text-slate-500">{isUser ? "我" : "归一"}</div>

      {isUser ? (
        <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
      ) : (
        <div className="markdown text-sm leading-6">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
        </div>
      )}

      {message.tools?.map((t) => (
        <div
          key={t.id}
          className="mt-2 rounded-lg border border-slate-200 bg-slate-50 p-2 text-xs"
        >
          <code>{t.name}</code>
          <span className="ml-2 text-slate-500">{t.status}</span>
          {t.summary && <div className="mt-1 text-slate-600">{t.summary}</div>}
        </div>
      ))}
    </div>
  );
}