import { useEffect, useState } from "react";
import ChatInput from "../components/chat/ChatInput";
import MessageList from "../components/chat/MessageList";
import QuotaBar from "../components/chat/QuotaBar";
import SourceInspector from "../components/chat/SourceInspector";
import WorkspaceHeader from "../components/chat/WorkspaceHeader";
import { useAuth } from "../context/AuthContext";
import { useChatStream } from "../hooks/useChatStream";
import { useWorkspace } from "../store/workspace";

/** 研究工作区：中央报告画布 + 右侧来源检查器，会话/消息状态来自全局 store。 */
export default function Chat() {
  const [input, setInput] = useState("");
  const { me, refresh: refreshMe } = useAuth();

  const messages = useWorkspace((s) => s.messages);
  const activeId = useWorkspace((s) => s.activeId);
  const ready = useWorkspace((s) => s.ready);
  const loading = useWorkspace((s) => s.loading);
  const storeError = useWorkspace((s) => s.error);
  const focusMode = useWorkspace((s) => s.focusMode);
  const inspectorOpen = useWorkspace((s) => s.inspectorOpen);
  const inspectorExpanded = useWorkspace((s) => s.inspectorExpanded);
  const setMessages = useWorkspace((s) => s.setMessages);
  const setActiveId = useWorkspace((s) => s.setActiveId);
  const setRunning = useWorkspace((s) => s.setRunning);
  const refresh = useWorkspace((s) => s.refresh);

  const { running, status, error, quotaExceeded, resetQuota, send, abort } = useChatStream({
    setMessages,
    conversationId: activeId,
    onConversation: setActiveId,
    onRoundDone: () => {
      void refresh();
      void refreshMe();
    },
  });

  // 把流式运行状态同步到全局，左导航据此禁用切换
  useEffect(() => {
    setRunning(running);
  }, [running, setRunning]);

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    resetQuota();
    void send(text);
  };

  const exhausted = quotaExceeded || (me?.quota ? me.quota.used >= me.quota.limit : false);
  // 检查器展开态：画布收窄至 740，输入区切换单行
  const expandedView = inspectorOpen && inspectorExpanded && !focusMode;

  return (
    <div className="chat-workspace flex min-w-0 flex-col lg:h-full lg:flex-row">
      <section className="flex min-w-0 flex-col lg:min-h-0 lg:flex-1">
        <WorkspaceHeader />

        <div className="lg:min-h-0 lg:flex-1">
          <MessageList
            messages={messages}
            status={loading ? "加载历史…" : status}
            error={storeError ?? error}
            onPick={setInput}
            focus={focusMode}
            expanded={expandedView}
          />
        </div>

        {me?.quota && (
          <div className="px-gutter-xl pb-gutter-sm">
            <QuotaBar used={me.quota.used} limit={me.quota.limit} exhausted={exhausted} />
          </div>
        )}

        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          onStop={abort}
          running={running}
          disabled={!ready || exhausted}
          variant={focusMode ? "focus" : expandedView ? "expanded" : "main"}
        />
      </section>

      {/* 窄屏与桌面均为内联堆叠/右栏，不使用浮层与遮罩 */}
      {inspectorOpen && !focusMode && <SourceInspector />}
    </div>
  );
}