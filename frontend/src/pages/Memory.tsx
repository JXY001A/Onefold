import { useMemo, useState } from "react";
import MemoryConfirmModal from "../components/memory/MemoryConfirmModal";
import MemoryDetailPanel from "../components/memory/MemoryDetailPanel";
import MemoryEditorModal from "../components/memory/MemoryEditorModal";
import MemoryHeader from "../components/memory/MemoryHeader";
import MemoryListItem from "../components/memory/MemoryListItem";
import MemoryStats, { type MemoryStatsData } from "../components/memory/MemoryStats";
import MemoryToolbar, { type MemoryFilters } from "../components/memory/MemoryToolbar";
import "../components/memory/memory.css";
import Icon from "../components/ui/Icon";
import { useMemory } from "../hooks/useMemory";
import type { MemoryItem } from "../lib/memory";
import { bucketOf, SUBCATEGORY_FILTERS } from "../lib/memoryCategories";
import { mockCitations } from "../lib/memoryMock";

const DEFAULT_FILTERS: MemoryFilters = {
  search: "",
  status: "all",
  type: "all",
  sort: "updated",
  category: "all",
};

type ConfirmState = { type: "single"; id: string } | { type: "clearAll" } | null;

/** 记忆中心（/memory）：按 onefold_memory_center 设计稿 1:1 重建，页面固定深色。
 * 编辑仅正文真实保存；分类/类型/激活只读；引用与停用为 mock（示例微标）。 */
export default function Memory() {
  const { data, loading, toggle, saveText, removeItem, clearAllItems, isActive, toggleActive } =
    useMemory();
  const [filters, setFilters] = useState<MemoryFilters>(DEFAULT_FILTERS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editing, setEditing] = useState<MemoryItem | null>(null);
  const [confirm, setConfirm] = useState<ConfirmState>(null);

  const items = useMemo(() => (data ? [...data.cards, ...data.notes] : []), [data]);
  const enabled = data?.enabled ?? false;

  const stats = useMemo<MemoryStatsData>(() => {
    let active = 0;
    let inactive = 0;
    let citations = 0;
    for (const item of items) {
      if (isActive(item)) active += 1;
      else inactive += 1;
      citations += mockCitations(item.id);
    }
    return { total: items.length, active, inactive, citations };
  }, [items, isActive]);

  const filtered = useMemo(() => {
    const q = filters.search.trim().toLowerCase();
    const isSub = (SUBCATEGORY_FILTERS as readonly string[]).includes(filters.category);
    return items
      .filter((m) => {
        if (filters.category !== "all") {
          if (isSub) {
            if ((m.category ?? "其他") !== filters.category) return false;
          } else if (bucketOf(m.category) !== filters.category) {
            return false;
          }
        }
        const eff = isActive(m);
        if (filters.status === "active" && !eff) return false;
        if (filters.status === "inactive" && eff) return false;
        if (filters.type !== "all" && m.kind !== filters.type) return false;
        if (q) {
          const hay = `${m.text} ${m.category ?? ""} ${bucketOf(m.category)}`.toLowerCase();
          if (!hay.includes(q)) return false;
        }
        return true;
      })
      .sort((a, b) => {
        if (filters.sort === "citations") return mockCitations(b.id) - mockCitations(a.id);
        if (filters.sort === "created") return (b.happened_at ?? "").localeCompare(a.happened_at ?? "");
        return (b.updated_at ?? "").localeCompare(a.updated_at ?? "");
      });
  }, [items, filters, isActive]);

  const activeId = filtered.some((m) => m.id === selectedId) ? selectedId : filtered[0]?.id ?? null;
  const selected = filtered.find((m) => m.id === activeId) ?? null;

  const confirmBody =
    confirm?.type === "single"
      ? {
          title: "删除这条记忆？",
          desc: "删除后该记忆将从记忆库移除，AI 在后续研究对话中不再引用该信息。",
          confirmText: "确认删除",
          run: () => {
            removeItem(confirm.id);
            setConfirm(null);
          },
        }
      : confirm?.type === "clearAll"
        ? {
            title: "清空全部记忆？",
            desc: "此操作将删除当前保存的全部记忆，删除后 AI 将无法在后续对话中继续召回你的背景、偏好与项目上下文，且无法撤销。",
            confirmText: "清空全部",
            run: () => {
              clearAllItems();
              setConfirm(null);
            },
          }
        : null;

  return (
    <div className="dark flex-1 overflow-y-auto bg-dark-background">
      <main className="mx-auto flex min-h-full w-full max-w-[1440px] flex-col gap-gutter-md px-gutter-lg py-gutter-lg text-dark-on-background">
        <MemoryHeader enabled={enabled} onToggleGlobal={toggle} onClearAll={() => setConfirm({ type: "clearAll" })} />

        {!loading && !enabled && (
          <div className="flex items-center justify-between gap-gutter-md rounded border border-dark-outline-variant bg-dark-surface-container-low px-gutter-md py-gutter-sm text-dark-on-surface-variant">
            <div className="flex items-center gap-gutter-sm">
              <Icon name="pause_circle" size={18} className="text-dark-outline" />
              <p className="font-body text-body-sm">
                全局记忆已关闭。所有记忆暂时不参与后续 AI 对话，各条记忆原本的启用状态已保留。
              </p>
            </div>
            <button type="button" onClick={toggle} className="shrink-0 font-label text-label-md text-dark-primary hover:underline">
              重新开启
            </button>
          </div>
        )}

        <MemoryStats stats={stats} />

        {loading ? (
          <p className="py-section text-center font-label text-label-sm text-dark-outline">加载记忆…</p>
        ) : (
          <section className="grid flex-1 grid-cols-1 items-start gap-gutter-lg lg:grid-cols-[1.85fr_1fr]">
            <div className="flex min-w-0 flex-col gap-gutter-md">
              <MemoryToolbar filters={filters} onChange={(patch) => setFilters((f) => ({ ...f, ...patch }))} />
              <div className="flex items-center justify-between px-1">
                <span className="font-label text-label-sm tabular-nums text-dark-on-surface-variant">
                  共 {filtered.length} 条记忆
                </span>
                <span className="font-mono text-mono-sm text-dark-outline">点击记忆查看详情 · 开关即时生效</span>
              </div>
              <div className="memory-scroll flex flex-col gap-gutter-sm pr-1 lg:max-h-[640px] lg:overflow-y-auto">
                {filtered.length === 0 ? (
                  <div className="flex flex-col items-center justify-center gap-gutter-sm rounded border border-dark-outline-variant bg-dark-surface px-gutter-xl py-section text-center">
                    <Icon name="inbox" size={28} className="text-dark-outline" />
                    <p className="font-body text-body-sm text-dark-on-surface-variant">当前筛选条件下暂无记忆</p>
                  </div>
                ) : (
                  filtered.map((item) => (
                    <MemoryListItem
                      key={item.id}
                      item={item}
                      selected={item.id === activeId}
                      effectiveActive={isActive(item)}
                      dimmed={!enabled}
                      onSelect={() => setSelectedId(item.id)}
                      onToggleActive={() => toggleActive(item)}
                      onEdit={() => setEditing(item)}
                      onDelete={() => setConfirm({ type: "single", id: item.id })}
                    />
                  ))
                )}
              </div>
            </div>

            {selected ? (
              <MemoryDetailPanel
                item={selected}
                effectiveActive={isActive(selected)}
                onEdit={() => setEditing(selected)}
                onDelete={() => setConfirm({ type: "single", id: selected.id })}
              />
            ) : (
              <aside
                aria-label="记忆详情"
                className="flex min-h-[360px] flex-col items-center justify-center gap-gutter-sm rounded border border-dark-outline-variant bg-dark-surface p-gutter-xl text-center lg:sticky lg:top-gutter-lg"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-dark-surface-container text-dark-outline">
                  <Icon name="psychology" size={22} />
                </span>
                <p className="font-body text-body-sm text-dark-on-surface-variant">选择一条记忆，查看详细信息</p>
              </aside>
            )}
          </section>
        )}
      </main>

      {editing && (
        <MemoryEditorModal
          item={editing}
          effectiveActive={isActive(editing)}
          onClose={() => setEditing(null)}
          onSave={(text) => saveText(editing.id, text)}
        />
      )}

      {confirmBody && (
        <MemoryConfirmModal
          title={confirmBody.title}
          desc={confirmBody.desc}
          confirmText={confirmBody.confirmText}
          onCancel={() => setConfirm(null)}
          onConfirm={confirmBody.run}
        />
      )}
    </div>
  );
}
