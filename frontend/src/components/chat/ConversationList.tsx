import type { Conversation } from "../../lib/chat";
import { formatTime } from "../../lib/chat";

type Props = {
  conversations: Conversation[];
  activeId: string | null;
  /** 生成中禁止切换会话：切换会让正在流式输出的消息无处安放 */
  disabled?: boolean;
  onSelect: (id: string) => void;
  onNew: () => void;
};

export default function ConversationList({
  conversations,
  activeId,
  disabled = false,
  onSelect,
  onNew,
}: Props) {
  return (
    <aside className="flex w-full shrink-0 flex-col gap-2 md:w-60">
      <button
        onClick={onNew}
        disabled={disabled}
        className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm hover:border-slate-500 disabled:opacity-50"
      >
        + 新对话
      </button>

      <nav className="max-h-[60vh] space-y-1 overflow-y-auto pr-1 md:max-h-[70vh]">
        {conversations.length === 0 && (
          <p className="px-1 py-4 text-xs text-slate-400">还没有历史会话（近 20 天）</p>
        )}
        {conversations.map((c) => {
          const active = c.id === activeId;
          return (
            <button
              key={c.id}
              onClick={() => onSelect(c.id)}
              disabled={disabled || active}
              title={c.title}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm transition ${
                active
                  ? "bg-slate-900 text-white"
                  : "text-slate-700 hover:bg-slate-200/70 disabled:opacity-60"
              }`}
            >
              <span className="block truncate">{c.title}</span>
              <span
                className={`block text-xs ${active ? "text-slate-300" : "text-slate-400"}`}
              >
                {formatTime(c.updatedAt)}
              </span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}