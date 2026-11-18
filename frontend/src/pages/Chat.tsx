import { useCallback, useEffect, useState } from "react";
import ChatInput from "../components/chat/ChatInput";
import ConversationList from "../components/chat/ConversationList";
import MessageList from "../components/chat/MessageList";
import { useChatStream } from "../hooks/useChatStream";
import { fetchConversations, fetchMessages, type Conversation } from "../lib/chat";
import { ensureSession } from "../lib/session";

export default function Chat() {
  const [input, setInput] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  const refreshConversations = useCallback(async () => {
    try {
      setConversations(await fetchConversations());
    } catch (e) {
      setPageError((e as Error).message);
    }
  }, []);

  const { messages, setMessages, running, status, error, send, abort } = useChatStream({
    conversationId: activeId,
    onConversation: setActiveId,
    onRoundDone: refreshConversations,
  });

  // 首次进入：确保请求有身份 → 拉会话列表 → 自动打开最近一个会话
  useEffect(() => {
    let cancelled = false;
    ensureSession()
      .then(() => fetchConversations())
      .then(async (list) => {
        if (cancelled) return;
        setConversations(list);
        if (list.length === 0) return;
        // 只打开第一个（后端已按活跃时间倒序）
        const latest = list[0].id;
        setActiveId(latest);
        setLoadingHistory(true);
        try {
          const history = await fetchMessages(latest);
          if (!cancelled) setMessages(history);
        } finally {
          if (!cancelled) setLoadingHistory(false);
        }
      })
      .catch((e) => {
        if (!cancelled) setPageError((e as Error).message);
      })
      .finally(() => {
        if (!cancelled) setReady(true);
      });
    return () => {
      cancelled = true;
    };
    // 只在挂载时执行一次；setMessages 是稳定的 state setter
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openConversation = async (id: string) => {
    if (running || id === activeId) return;
    setLoadingHistory(true);
    setPageError(null);
    try {
      const history = await fetchMessages(id);
      setActiveId(id);
      setMessages(history);
    } catch (e) {
      setPageError((e as Error).message);
    } finally {
      setLoadingHistory(false);
    }
  };

  const newChat = () => {
    if (running) return;
    setActiveId(null);
    setMessages([]);
    setInput("");
    setPageError(null);
  };

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    void send(text);
  };

  return (
    <div className="flex flex-col gap-4 md:flex-row">
      <ConversationList
        conversations={conversations}
        activeId={activeId}
        disabled={running || !ready}
        onSelect={openConversation}
        onNew={newChat}
      />

      <div className="flex-1 space-y-4">
        <MessageList
          messages={messages}
          status={loadingHistory ? "加载历史…" : status}
          error={pageError ?? error}
        />
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          onStop={abort}
          running={running}
          disabled={!ready}
        />
      </div>
    </div>
  );
}