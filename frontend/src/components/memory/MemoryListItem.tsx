import type { KeyboardEvent } from "react";
import type { MemoryItem } from "../../lib/memory";
import { bucketOf } from "../../lib/memoryCategories";
import { kindLabel, memoryDateTime } from "../../lib/memoryDisplay";
import { mockCitations, mockLastCitedAt } from "../../lib/memoryMock";
import Icon from "../ui/Icon";

/** mock 字段的「示例」微标（口径：仅字段微标，不占页面级空间）。 */
function MockTag() {
  return <span className="font-mono text-[10px] text-dark-outline">示例</span>;
}

type Props = {
  item: MemoryItem;
  selected: boolean;
  /** 有效激活状态（真实默认 + mock 停用 + 内存切换） */
  effectiveActive: boolean;
  /** 全局记忆关闭时整卡降透明度 */
  dimmed: boolean;
  onSelect: () => void;
  onToggleActive: () => void;
  onEdit: () => void;
  onDelete: () => void;
};

/** 记忆中心列表卡：设计稿三行结构（分类/类型/时间 + 状态开关 / 正文 / 引用与操作）。 */
export default function MemoryListItem({
  item,
  selected,
  effectiveActive,
  dimmed,
  onSelect,
  onToggleActive,
  onEdit,
  onDelete,
}: Props) {
  const citations = mockCitations(item.id);
  const lastCited = mockLastCitedAt(item.id);

  const onKeyDown = (e: KeyboardEvent<HTMLElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect();
    }
  };

  return (
    <article
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      onClick={onSelect}
      onKeyDown={onKeyDown}
      className={`flex cursor-pointer flex-col gap-gutter-sm rounded border p-gutter-md transition-colors duration-state-change focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-dark-primary ${
        selected
          ? "border-dark-primary bg-dark-surface-container"
          : "border-dark-outline-variant bg-dark-surface hover:bg-dark-surface-container"
      } ${dimmed ? "opacity-75" : ""}`}
    >
      {/* Row 1 */}
      <div className="flex items-center justify-between gap-gutter-sm">
        <div className="flex flex-wrap items-center gap-gutter-sm">
          <span className="rounded-sm bg-dark-primary-container px-2 py-0.5 font-label text-label-sm text-dark-on-primary-container">
            {bucketOf(item.category)}
          </span>
          <span className="rounded-sm border border-dark-outline-variant bg-dark-surface-container-low px-2 py-0.5 font-label text-label-sm text-dark-on-surface-variant">
            {kindLabel(item.kind)}
          </span>
          <span className="font-mono text-mono-sm tabular-nums text-dark-outline">
            更新于 {memoryDateTime(item.updated_at)}
          </span>
        </div>
        <div className="flex shrink-0 items-center gap-gutter-xs">
          <span
            className={`flex items-center gap-1 font-label text-label-sm ${
              effectiveActive ? "text-dark-success" : "text-dark-outline"
            }`}
          >
            {effectiveActive ? "已激活" : "已停用"}
            {!effectiveActive && <MockTag />}
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={effectiveActive}
            aria-label="切换单条记忆激活状态"
            onClick={(e) => {
              e.stopPropagation();
              onToggleActive();
            }}
            className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-state-change ${
              effectiveActive ? "bg-dark-success" : "bg-dark-surface-container-highest"
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-3.5 w-3.5 rounded-full transition-transform duration-state-change ${
                effectiveActive ? "translate-x-[18px] bg-dark-on-success" : "translate-x-[3px] bg-dark-on-surface-variant"
              }`}
            />
          </button>
        </div>
      </div>

      {/* Row 2 */}
      <p className="line-clamp-2 font-body text-body-sm text-dark-on-surface">{item.text}</p>

      {/* Row 3 */}
      <div className="flex items-center justify-between gap-gutter-sm pt-0.5">
        <div className="flex flex-wrap items-center gap-gutter-md">
          <span
            className={`inline-flex items-center gap-1 font-mono text-mono-sm tabular-nums ${
              citations > 0 ? "text-dark-primary" : "text-dark-outline"
            }`}
          >
            <Icon name="format_quote" size={14} />
            被引用 {citations} 次 <MockTag />
          </span>
          {citations > 0 && lastCited && (
            <span className="flex items-center gap-1 font-mono text-mono-sm tabular-nums text-dark-outline">
              最近引用 {lastCited} <MockTag />
            </span>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-gutter-sm">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onEdit();
            }}
            className="rounded-sm px-2 py-0.5 font-label text-label-sm text-dark-on-surface-variant transition-colors hover:bg-dark-surface-container-high hover:text-dark-on-surface"
          >
            编辑
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="rounded-sm px-2 py-0.5 font-label text-label-sm text-dark-error transition-colors hover:bg-dark-surface-container-high"
          >
            删除
          </button>
        </div>
      </div>
    </article>
  );
}
