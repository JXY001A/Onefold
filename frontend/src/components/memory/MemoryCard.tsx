import type { MemoryItem } from "../../lib/memory";
import { kindLabel, memoryDate } from "../../lib/memoryDisplay";
import { Badge } from "../ui/kit";

type Props = {
  item: MemoryItem;
  active: boolean;
  memoryEnabled: boolean;
  onSelect: () => void;
  onEdit: () => void;
  onRemove: () => void;
};

/** 2.0 记忆行：分类/类型/日期/次数/固定徽章 + 正文；来源会话等缺失字段省略。 */
export default function MemoryCard({ item, active, memoryEnabled, onSelect, onEdit, onRemove }: Props) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
      className={`flex cursor-pointer flex-col gap-2 border-b border-light-outline-variant px-gutter-md py-gutter-md last:border-0 dark:border-dark-outline-variant ${
        active ? "bg-light-surface-container dark:bg-dark-surface-container" : "hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container-low"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-gutter-sm">
        <div className="flex min-w-0 flex-wrap items-center gap-2 font-label text-label-sm text-light-outline dark:text-dark-outline">
          <Badge>{item.category ?? "其他"}</Badge>
          <span>{kindLabel(item.kind)} · {memoryDate(item.updated_at)}</span>
          {item.mention_count > 1 && <span>提到 {item.mention_count} 次</span>}
          {item.pinned && <Badge tone="primary">已固定</Badge>}
        </div>
        <span className={`inline-flex shrink-0 items-center gap-1 font-label text-label-sm ${memoryEnabled ? "text-light-primary dark:text-dark-primary" : "text-light-on-surface-variant dark:text-dark-on-surface-variant"}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${memoryEnabled ? "bg-light-primary dark:bg-dark-primary" : "bg-light-outline dark:bg-dark-outline"}`} />
          {memoryEnabled ? "已启用" : "已停用"}
        </span>
      </div>

      <p className="whitespace-pre-wrap font-body text-body-sm text-light-on-surface dark:text-dark-on-surface">{item.text}</p>

      <div className="flex items-center gap-gutter-md">
        <Action label="编辑" onClick={onEdit} />
        <Action label="删除" tone="text-light-error dark:text-dark-error" onClick={onRemove} />
      </div>
    </div>
  );
}

function Action({ label, tone = "text-light-on-surface-variant dark:text-dark-on-surface-variant", onClick }: { label: string; tone?: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className={`underline underline-offset-2 font-label text-label-sm ${tone}`}
    >
      {label}
    </button>
  );
}
