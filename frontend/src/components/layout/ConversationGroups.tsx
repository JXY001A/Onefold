import { useNavigate } from "react-router-dom";
import { formatTime, type Conversation } from "../../lib/chat";
import { useWorkspace } from "../../store/workspace";

/** 自然周（周一开始）：今天 / 本周 / 更早。 */
function groupOf(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "更早";
  const now = new Date();
  const startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const mondayOffset = (now.getDay() + 6) % 7;
  const startWeek = startToday - mondayOffset * 86400000;
  const t = d.getTime();
  if (t >= startToday) return "今天";
  if (t >= startWeek) return "本周";
  return "更早";
}

const ORDER = ["今天", "本周", "更早"];

/** 左导航会话列表：自然周分组 + 当前会话高亮（主色圆点 + 描边）。 */
export default function ConversationGroups({ compact = false }: { compact?: boolean }) {
  const navigate = useNavigate();
  const conversations = useWorkspace((s) => s.conversations);
  const activeId = useWorkspace((s) => s.activeId);
  const running = useWorkspace((s) => s.running);
  const open = useWorkspace((s) => s.open);

  const groups = ORDER.map((label) => ({
    label,
    items: conversations.filter((c) => groupOf(c.updatedAt) === label),
  })).filter((g) => g.items.length > 0);

  const select = (c: Conversation) => {
    void open(c.id);
    navigate("/chat");
  };

  if (conversations.length === 0) {
    return <p className="px-gutter-sm py-gutter-sm font-label text-label-sm text-light-outline dark:text-dark-outline">还没有历史会话（近 20 天）</p>;
  }

  return (
    <div className="flex flex-col gap-gutter-md">
      {groups.map((g) => (
        <div key={g.label} className="flex flex-col gap-0.5">
          <span className="px-gutter-sm pb-1 font-label text-label-sm text-light-outline dark:text-dark-outline">{g.label}</span>
          {g.items.map((c) => {
            const active = c.id === activeId;
            return (
              <button
                key={c.id}
                type="button"
                title={c.title}
                disabled={running}
                onClick={() => select(c)}
                className={`flex w-full items-center justify-between gap-1 rounded px-gutter-sm py-1.5 text-left transition-colors duration-state-change disabled:opacity-60 ${
                  active
                    ? "border border-light-outline-variant bg-light-surface dark:border-transparent dark:bg-dark-surface-container"
                    : "border border-transparent hover:bg-light-surface-container-high dark:hover:bg-dark-surface-container-high"
                }`}
              >
                <span className="flex min-w-0 items-center gap-1">
                  {active && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-light-primary dark:bg-dark-primary" />}
                  <span className={`min-w-0 truncate font-label text-label-md ${active ? "pl-1 text-light-on-surface dark:text-dark-on-surface" : "pl-3.5 text-light-on-surface-variant dark:text-dark-on-surface-variant"}`}>
                    {c.title}
                  </span>
                </span>
                {!compact && <span className="shrink-0 font-mono text-mono-sm tabular-nums text-light-outline dark:text-dark-outline">{formatTime(c.updatedAt)}</span>}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}
