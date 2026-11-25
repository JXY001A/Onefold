import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../../lib/chat";
import RetrievalStatus from "./RetrievalStatus";
import ToolDrawer from "./ToolDrawer";

type Props = {
  message: ChatMessage;
  /** 专注态：问题显示为上下文行，不显示提问卡 */
  focus?: boolean;
  /** 检查器展开态：画布不显示提问卡 */
  expanded?: boolean;
};

/** 单条消息：提问卡 / 专注问题行；助手报告按设计稿编辑式排版（无核心结论标记则不套竖线）。 */
export default function MessageItem({ message, focus = false, expanded = false }: Props) {
  const [open, setOpen] = useState(false);
  const tools = message.tools ?? [];

  if (message.role === "user") {
    if (expanded) return null;
    if (focus) {
      return (
        <div className="border-b border-light-outline-variant pb-gutter-md dark:border-dark-outline-variant">
          <span className="font-label text-label-sm text-light-outline dark:text-dark-outline">研究问题：</span>
          <span className="whitespace-pre-wrap font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">{message.content}</span>
        </div>
      );
    }
    return (
      <div className="rounded-md border border-light-outline-variant bg-light-surface-container p-gutter-md dark:border-dark-outline-variant dark:bg-dark-surface-container">
        <p className="whitespace-pre-wrap font-body text-body-md text-light-on-surface dark:text-dark-on-surface">{message.content}</p>
      </div>
    );
  }

  return (
    <article className="flex flex-col gap-gutter-md">
      {/* 专注/展开画布按设计稿不显示检索卡与提问卡 */}
      {!focus && !expanded && <RetrievalStatus tools={tools} onOpenDetails={() => setOpen(true)} />}

      <div className="chat-report font-body text-body-md text-light-on-surface dark:text-dark-on-surface">
        {/* singleTilde:false —— 否则「5~12℃」这类区间会被 GFM 当成删除线吞掉 */}
        <ReactMarkdown remarkPlugins={[[remarkGfm, { singleTilde: false }]]}>{message.content}</ReactMarkdown>
        {message.content === "" && <span className="of-caret" />}
      </div>

      {open && tools.length > 0 && <ToolDrawer tools={tools} onClose={() => setOpen(false)} />}
    </article>
  );
}
