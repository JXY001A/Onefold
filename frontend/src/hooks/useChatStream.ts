import { useCallback, useRef, useState } from "react";
import type { ChatMessage } from "../lib/chat";
import { streamChat } from "../lib/sse";

type Options = {
  /** 当前会话 ID；null 表示新会话（首轮结束后由 meta 事件回填） */
  conversationId: string | null;
  /** 首轮由后端新建会话后回填 ID，页面据此记住当前会话 */
  onConversation: (id: string) => void;
  /** 一轮结束后回调（刷新侧栏排序与标题） */
  onRoundDone?: () => void;
};

/** 流式对话状态机：消息、运行状态、错误与中止，全部收在这里，页面只做编排。 */
export function useChatStream({ conversationId, onConversation, onRoundDone }: Options) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const ctrl = useRef<AbortController | null>(null);

  // 流式输出期间只改「最后一条 assistant 消息」，历史消息不受影响
  const patchLast = useCallback((fn: (m: ChatMessage) => ChatMessage) => {
    setMessages((prev) => {
      const idx = prev.map((m) => m.role).lastIndexOf("assistant");
      if (idx < 0) return prev;
      const next = prev.slice();
      next[idx] = fn(next[idx]);
      return next;
    });
  }, []);

  const send = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content || running) return;

      setError(null);
      setStatus("");
      setMessages((prev) => [
        ...prev,
        { role: "user", content },
        { role: "assistant", content: "", tools: [] },
      ]);

      const controller = new AbortController();
      ctrl.current = controller;
      setRunning(true);

      try {
        for await (const ev of streamChat(
          { message: content, conversation_id: conversationId ?? undefined },
          { signal: controller.signal },
        )) {
          if (ev.type === "meta") {
            if (ev.conversationId) onConversation(ev.conversationId);
          } else if (ev.type === "queue") {
            setStatus("排队中…");
          } else if (ev.type === "token") {
            setStatus("");
            patchLast((m) => ({ ...m, content: m.content + ev.delta }));
          } else if (ev.type === "tool_call") {
            patchLast((m) => ({
              ...m,
              tools: [...(m.tools ?? []), { id: ev.id, name: ev.name, status: "running" }],
            }));
          } else if (ev.type === "tool_result") {
            patchLast((m) => ({
              ...m,
              tools: (m.tools ?? []).map((t) =>
                t.id === ev.id
                  ? { ...t, status: ev.ok ? "ok" : "error", summary: ev.summary }
                  : t,
              ),
            }));
          } else if (ev.type === "error") {
            setError(ev.message);
            setStatus("");
          }
        }
      } catch (e) {
        // 用户主动停止会产生 AbortError，不算错误
        if ((e as Error).name !== "AbortError") setError((e as Error).message);
      } finally {
        setRunning(false);
        ctrl.current = null;
        setStatus("");
        onRoundDone?.();
      }
    },
    [conversationId, onConversation, onRoundDone, patchLast, running],
  );

  const abort = useCallback(() => ctrl.current?.abort(), []);

  return { messages, setMessages, running, status, error, send, abort };
}