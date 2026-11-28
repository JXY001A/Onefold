import { useState } from "react";
import { CATEGORY_BUCKETS, SUBCATEGORY_FILTERS } from "../../lib/memoryCategories";
import Icon from "../ui/Icon";

/** 记忆中心的筛选状态（页面持有，工具栏只负责展示与回调）。 */
export type MemoryFilters = {
  search: string;
  status: "all" | "active" | "inactive";
  type: "all" | "note" | "card";
  sort: "updated" | "created" | "citations";
  /** 'all' | 6 大桶标签 | 细分原分类 */
  category: string;
};

type Props = {
  filters: MemoryFilters;
  onChange: (patch: Partial<MemoryFilters>) => void;
};

const selectCls =
  "px-3 py-1.5 rounded bg-dark-surface border border-dark-outline-variant font-label text-label-sm text-dark-on-surface focus:border-dark-primary focus:ring-0";

/** 工具栏：搜索 + 状态/类型/排序 + 分类 pills（6 大桶，「更多」展开细分，可收起）。 */
export default function MemoryToolbar({ filters, onChange }: Props) {
  const [expanded, setExpanded] = useState(false);

  const pillCls = (on: boolean) =>
    `px-2.5 py-1 rounded-sm font-label text-label-sm transition-colors duration-state-change ${
      on
        ? "bg-dark-primary-container text-dark-on-primary-container"
        : "bg-dark-surface text-dark-on-surface-variant hover:bg-dark-surface-container"
    }`;

  return (
    <div className="flex flex-col gap-gutter-sm rounded border border-dark-outline-variant bg-dark-surface-container-low p-gutter-md">
      {/* 第一行：搜索 + 三个下拉 */}
      <div className="flex flex-col gap-gutter-sm md:flex-row md:items-center">
        <div className="relative min-w-[200px] flex-1">
          <Icon
            name="search"
            size={18}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dark-outline"
          />
          <input
            type="text"
            value={filters.search}
            onChange={(e) => onChange({ search: e.target.value })}
            placeholder="搜索记忆内容..."
            className="w-full rounded border border-dark-outline-variant bg-dark-surface py-1.5 pl-9 pr-3 font-body text-body-sm text-dark-on-surface placeholder:text-dark-outline focus:border-dark-primary focus:ring-0"
          />
        </div>

        <div className="flex flex-wrap items-center gap-gutter-sm">
          <select
            aria-label="状态筛选"
            value={filters.status}
            onChange={(e) => onChange({ status: e.target.value as MemoryFilters["status"] })}
            className={selectCls}
          >
            <option value="all">状态：全部</option>
            <option value="active">已激活</option>
            <option value="inactive">已停用</option>
          </select>

          <select
            aria-label="记忆类型筛选"
            value={filters.type}
            onChange={(e) => onChange({ type: e.target.value as MemoryFilters["type"] })}
            className={selectCls}
          >
            <option value="all">类型：全部</option>
            <option value="note">笔记记忆</option>
            <option value="card">卡片记忆</option>
          </select>

          <select
            aria-label="排序方式"
            value={filters.sort}
            onChange={(e) => onChange({ sort: e.target.value as MemoryFilters["sort"] })}
            className={selectCls}
          >
            <option value="updated">排序：最近更新</option>
            <option value="created">排序：创建时间</option>
            <option value="citations">排序：引用次数</option>
          </select>
        </div>
      </div>

      {/* 第二行：分类 pills */}
      <div className="flex flex-wrap items-center gap-gutter-xs" role="tablist" aria-label="记忆分类筛选">
        <button type="button" onClick={() => onChange({ category: "all" })} className={pillCls(filters.category === "all")}>
          全部
        </button>
        {CATEGORY_BUCKETS.map((bucket) => (
          <button
            key={bucket.label}
            type="button"
            onClick={() => onChange({ category: bucket.label })}
            className={pillCls(filters.category === bucket.label)}
          >
            {bucket.label}
          </button>
        ))}
        <button
          type="button"
          aria-expanded={expanded}
          onClick={() => setExpanded((v) => !v)}
          className={`${pillCls(false)} inline-flex items-center gap-0.5`}
        >
          {expanded ? "收起" : "更多"}
          <Icon name={expanded ? "expand_less" : "expand_more"} size={14} />
        </button>
      </div>

      {/* 「更多」展开：细分原分类 */}
      {expanded && (
        <div className="flex flex-wrap items-center gap-gutter-xs border-t border-dark-outline-variant pt-gutter-sm">
          {SUBCATEGORY_FILTERS.map((sub) => (
            <button
              key={sub}
              type="button"
              onClick={() => onChange({ category: sub })}
              className={pillCls(filters.category === sub)}
            >
              {sub}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
