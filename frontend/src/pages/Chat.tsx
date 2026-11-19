import { useState } from "react";
import ChatInput from "../components/chat/ChatInput";
import ConversationList from "../components/chat/ConversationList";
import MessageList from "../components/chat/MessageList";
import QuotaBar from "../components/chat/QuotaBar";
import { useAuth } from "../context/AuthContext";
import { useChatStream } from "../hooks/useChatStream";
import { useConversations } from "../hooks/useConversations";
import type { ChatMessage } from "../lib/chat";

export default function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { me, refresh: refreshMe } = useAuth();

  // 会话列表/历史加载与流式状态分开，页面只做编排
  const convs = useConversations(setMessages);
  const { running, status, error, quotaExceeded, resetQuota, send, abort } = useChatStream({
    setMessages,
    conversationId: convs.activeId,
    onConversation: convs.setActiveId,
    onRoundDone: () => {
      void convs.refresh();
      void refreshMe();
    },
  });

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    void send(text);
  };

  const openConversation = (id: string) => {
    if (running) return;
    void convs.open(id);
  };

  const newChat = () => {
    if (running) return;
    convs.startNew();
    setInput("");
    resetQuota();
  };

  // 后端 403 或本地计数已满都算用完，避免多发一次注定失败的请求
  const exhausted = quotaExceeded || (me?.quota ? me.quota.used >= me.quota.limit : false);

  return (
    <div className="flex flex-col gap-4 md:flex-row">
      <ConversationList
        conversations={convs.conversations}
        activeId={convs.activeId}
        disabled={running || !convs.ready}
        onSelect={openConversation}
        onNew={newChat}
      />

      <div className="flex-1 space-y-4">
        <MessageList
          messages={messages}
          status={convs.loading ? "加载历史…" : status}
          error={convs.error ?? error}
        />
        {me?.quota && (
          <QuotaBar used={me.quota.used} limit={me.quota.limit} exhausted={exhausted} />
        )}
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          onStop={abort}
          running={running}
          disabled={!convs.ready || exhausted}
        />
      </div>
    </div>
  );
}