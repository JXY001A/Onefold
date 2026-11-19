import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../../lib/chat";
import ToolDrawer from "./ToolDrawer";
import ToolStatus from "./ToolStatus";

/** 单条消息：用户消息保留换行原样展示，助手消息按 Markdown 渲染（含表格/任务列表）。 */
export default function MessageItem({ message }: { message: ChatMessage }) {
  const [open, setOpen] = useState(false);
  const isUser = message.role === "user";
  const tools = message.tools ?? [];

  return (
    <>
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        {/* 工具痕迹收在右上角，点开右侧抽屉看链接与简介 */}
        <div className="mb-2 flex items-center justify-between gap-2">
          <span className="text-xs font-medium text-slate-500">{isUser ? "我" : "归一"}</span>
          {tools.length > 0 && <ToolStatus tools={tools} onClick={() => setOpen(true)} />}
        </div>

        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
        ) : (
          <div className="markdown text-sm leading-6">
            {/* singleTilde: false —— 否则「5~12℃」这类区间会被 GFM 当成删除线吞掉 */}
            <ReactMarkdown remarkPlugins={[[remarkGfm, { singleTilde: false }]]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>

      {open && tools.length > 0 && (
        <ToolDrawer tools={tools} onClose={() => setOpen(false)} />
      )}
    </>
  );
}
