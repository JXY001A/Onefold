import { useMemo, useState } from "react";
import MemoryCard from "../components/memory/MemoryCard";
import MemoryInspector from "../components/memory/MemoryInspector";
import PageWorkspace from "../components/pages/PageWorkspace";
import Icon from "../components/ui/Icon";
import Soon from "../components/ui/Soon";
import { ActionLink, PageHeader, Tabs } from "../components/ui/kit";
import { useMemory } from "../hooks/useMemory";

/** 研究记忆（2.0 视觉壳 + 真实数据）：添加约束/来源会话/作用范围按决议省略。 */
export default function Memory() {
  const { data, loading, toggle, edit, remove, clearAll } = useMemory();
  const [tab, setTab] = useState("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const items = useMemo(() => {
    if (!data) return [];
    return [...data.cards, ...data.notes].sort((a, b) => (b.updated_at ?? "").localeCompare(a.updated_at ?? ""));
  }, [data]);

  const categories = useMemo(() => {
    const counts = new Map<string, number>();
    items.forEach((m) => {
      const key = m.category ?? "其他";
      counts.set(key, (counts.get(key) ?? 0) + 1);
    });
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [items]);

  const activeTab = tab === "all" || categories.some(([name]) => `c:${name}` === tab) ? tab : "all";
  const visible = activeTab === "all" ? items : items.filter((m) => `c:${m.category ?? "其他"}` === activeTab);
  const activeId = visible.some((m) => m.id === selectedId) ? selectedId : visible[0]?.id ?? null;
  const selected = visible.find((m) => m.id === activeId) ?? null;
  const enabled = data?.enabled ?? false;

  const tabs = [{ key: "all", label: `全部记忆 · ${items.length}` }, ...categories.map(([name, n]) => ({ key: `c:${name}`, label: `${name} · ${n}` }))];

  return (
    <PageWorkspace aside={<MemoryInspector item={selected} memoryEnabled={enabled} />}>
      <div className="flex flex-col gap-gutter-lg">
        <PageHeader
          title="研究记忆"
          desc="已启用的研究记忆会在检索重排与综合报告生成时自动生效。"
          actions={
            <>
              <Soon tip="添加记忆约束随后开放" place="bottom">
                <span className="inline-flex items-center gap-1.5 rounded bg-light-primary px-gutter-md py-2 font-label text-label-md text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary">
                  <Icon name="add" size={16} />
                  添加记忆约束
                </span>
              </Soon>
              <ActionLink onClick={toggle}>{enabled ? "关闭记忆" : "开启记忆"}</ActionLink>
              <ActionLink tone="danger" onClick={clearAll}>清空</ActionLink>
            </>
          }
        />

        {loading && <p className="py-section text-center font-label text-label-sm text-light-outline dark:text-dark-outline">加载记忆…</p>}
        {!loading && !data && <p className="py-section text-center font-label text-label-sm text-light-error dark:text-dark-error">记忆暂时取不到，请稍后刷新页面重试。</p>}

        {!loading && data && (
          <>
            {!enabled && (
              <p className="rounded border border-light-warning bg-light-warning-container px-gutter-md py-gutter-sm font-body text-body-sm text-light-on-warning-container dark:border-dark-warning dark:bg-dark-warning-container dark:text-dark-on-warning-container">
                记忆已关闭：不会提取新记忆，也不会注入已有记忆。
              </p>
            )}

            <Tabs tabs={tabs} active={activeTab} onChange={setTab} />

            <div className="overflow-hidden rounded border border-light-outline-variant bg-light-surface dark:border-dark-outline-variant dark:bg-dark-surface">
              {visible.length === 0 ? (
                <p className="px-gutter-md py-section text-center font-label text-label-sm text-light-outline dark:text-dark-outline">
                  {activeTab === "all" ? "暂无记忆。" : "该分类下暂无记忆。"}
                </p>
              ) : (
                visible.map((m) => (
                  <MemoryCard
                    key={m.id}
                    item={m}
                    active={m.id === activeId}
                    memoryEnabled={enabled}
                    onSelect={() => setSelectedId(m.id)}
                    onEdit={() => edit(m)}
                    onRemove={() => remove(m)}
                  />
                ))
              )}
            </div>
          </>
        )}
      </div>
    </PageWorkspace>
  );
}
