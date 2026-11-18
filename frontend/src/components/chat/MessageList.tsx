import { useEffect, useRef } from "react";
import type { ChatMessage } from "../../lib/chat";
import MessageItem from "./MessageItem";

type Props = {
  messages: ChatMessage[];
  status?: string;
  error?: string | null;
};

/** 消息区：新消息或流式内容变化时自动滚到底部。 */
export default function MessageList({ messages, status, error }: Props) {
  const endRef = useRef<HTMLDivElement>(null);
  // 内容变化（流式追加）也要触发滚动，所以依赖里带上最后一条消息的长度
  const tail = messages[messages.length - 1];

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages.length, tail?.content, status, error]);

  return (
    <div className="min-h-[50vh] space-y-4">
      {messages.length === 0 && (
        <p className="py-16 text-center text-sm text-slate-500">
          问一个问题，或从左侧选一个历史会话继续。
        </p>
      )}

      {messages.map((m, i) => (
        <MessageItem key={i} message={m} />
      ))}

      {status && <p className="text-center text-sm text-slate-500">{status}</p>}
      {error && <p className="text-center text-sm text-red-600">{error}</p>}

      <div ref={endRef} />
    </div>
  );
}