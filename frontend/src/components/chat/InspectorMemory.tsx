import { useNavigate } from "react-router-dom";
import { useMemory } from "../../hooks/useMemory";

/** 检查器「记忆」面板：只读展示真实记忆，入口保留到研究记忆页。 */
export default function InspectorMemory() {
  const navigate = useNavigate();
  const { data, loading } = useMemory();
  const items = data ? [...data.cards, ...data.notes] : [];

  if (loading) return <p className="font-label text-label-sm text-light-outline dark:text-dark-outline">加载中…</p>;

  return (
    <div className="flex flex-col gap-gutter-md">
      {items.length === 0 && (
        <p className="font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">还没有保存的记忆。对话中提到的偏好与背景会出现在这里。</p>
      )}
      {items.map((m) => (
        <div key={m.id} className="flex flex-col gap-1 border-b border-light-outline-variant pb-gutter-md last:border-0 last:pb-0 dark:border-dark-outline-variant">
          <span className="font-mono text-mono-sm tabular-nums text-light-outline dark:text-dark-outline">{m.updated_at ? m.updated_at.slice(0, 10) : "未记录日期"}</span>
          <p className="font-body text-body-sm text-light-on-surface dark:text-dark-on-surface">{m.text}</p>
        </div>
      ))}
      <button type="button" onClick={() => navigate("/memory")} className="self-start font-label text-label-sm text-light-primary underline underline-offset-2 dark:text-dark-primary">
        管理研究记忆
      </button>
    </div>
  );
}
