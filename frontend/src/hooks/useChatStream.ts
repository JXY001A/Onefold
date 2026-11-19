import { useCallback, useRef, useState, type Dispatch, type SetStateAction } from "react";
import type { ChatMessage, ToolRun } from "../lib/chat";
import { isQuotaError, streamChat } from "../lib/sse";

type Options = {
  /** 消息状态由页面持有：历史加载与流式追加都写同一份 */
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>;
  /** 当前会话 ID；null 表示新会话（首轮结束后由 meta 事件回填） */
  conversationId: string | null;
  /** 首轮由后端新建会话后回填 ID，页面据此记住当前会话 */
  onConversation: (id: string) => void;
  /** 一轮结束后回调（刷新侧栏排序、标题与配额） */
  onRoundDone?: () => void;
};

/** 流式对话状态机：运行状态、错误与中止收在这里，消息本身由页面持有。 */
export function useChatStream({ setMessages, conversationId, onConversation, onRoundDone }: Options) {
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  /** 游客免费轮次用完：后端在鉴权阶段直接 403，本轮不会落库 */
  const [quotaExceeded, setQuotaExceeded] = useState(false);
  const ctrl = useRef<AbortController | null>(null);

  // 流式输出期间只改「最后一条 assistant 消息」，历史消息不受影响
  const patchLast = useCallback(
    (fn: (m: ChatMessage) => ChatMessage) => {
      setMessages((prev) => {
        const idx = prev.map((m) => m.role).lastIndexOf("assistant");
        if (idx < 0) return prev;
        const next = prev.slice();
        next[idx] = fn(next[idx]);
        return next;
      });
    },
    [setMessages],
  );

  /** 请求被拒（未落库）时把刚插入的问答对撤掉，避免刷新后消息消失 */
  const rollback = useCallback(() => {
    setMessages((prev) => {
      const next = prev.slice();
      const tail = next[next.length - 1];
      if (tail?.role === "assistant" && !tail.content) next.pop();
      if (next[next.length - 1]?.role === "user") next.pop();
      return next;
    });
  }, [setMessages]);

  const send = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content || running || quotaExceeded) return;

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
            setStatus(""); // 已经在跑工具，别再显示「排队中」
            const chip: ToolRun = { id: ev.id, name: ev.name, status: "running", args: ev.arguments };
            patchLast((m) => ({ ...m, tools: [...(m.tools ?? []), chip] }));
          } else if (ev.type === "tool_result") {
            patchLast((m) => ({
              ...m,
              tools: (m.tools ?? []).map((t) =>
                t.id === ev.id ? { ...t, status: ev.ok ? "ok" : "error", summary: ev.summary, data: ev.detail } : t,
              ),
            }));
          } else if (ev.type === "error") {
            setError(ev.message);
            setStatus("");
          }
        }
      } catch (e) {
        const err = e as Error;
        if (isQuotaError(err)) {
          setQuotaExceeded(true);
          rollback();
        } else if (err.name !== "AbortError") {
          // 用户主动停止会产生 AbortError，不算错误
          setError(err.message);
        }
      } finally {
        setRunning(false);
        ctrl.current = null;
        setStatus("");
        onRoundDone?.();
      }
    },
    [conversationId, onConversation, onRoundDone, patchLast, quotaExceeded, rollback, running, setMessages],
  );

  const abort = useCallback(() => ctrl.current?.abort(), []);

  return { running, status, error, quotaExceeded, resetQuota: () => setQuotaExceeded(false), send, abort };
}
