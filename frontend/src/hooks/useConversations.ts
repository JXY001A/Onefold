import { useCallback, useEffect, useRef, useState } from "react";
import { fetchConversations, fetchMessages, type ChatMessage, type Conversation } from "../lib/chat";
import { ensureSession } from "../lib/session";

type SetMessages = (messages: ChatMessage[]) => void;

/** 侧栏会话列表 + 历史消息：进入页面自动打开最近一个，切走/新建都走这里。 */
export function useConversations(setMessages: SetMessages) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // setMessages 是稳定 setter，但放进依赖会让 effect 重跑，用 ref 取最新值
  const setMessagesRef = useRef(setMessages);
  setMessagesRef.current = setMessages;

  const refresh = useCallback(async () => {
    try {
      setConversations(await fetchConversations());
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  const open = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const history = await fetchMessages(id);
      setActiveId(id);
      setMessagesRef.current(history);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  const startNew = useCallback(() => {
    setActiveId(null);
    setError(null);
    setMessagesRef.current([]);
  }, []);

  // 首次进入：确保有身份 → 拉列表 → 自动打开最近一个会话
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await ensureSession();
        const list = await fetchConversations();
        if (cancelled) return;
        setConversations(list);
        const latest = list[0];
        if (!latest) return;
        const history = await fetchMessages(latest.id).catch(() => null);
        if (cancelled || !history) return;
        setActiveId(latest.id);
        setMessagesRef.current(history);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return {
    conversations,
    activeId,
    setActiveId,
    loading,
    ready,
    error,
    setError,
    refresh,
    open,
    startNew,
  };
}
