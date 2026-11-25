import MemoryCard from "../components/memory/MemoryCard";
import { ActionLink, EmptyText, PageHeader } from "../components/ui/kit";
import { useMemory } from "../hooks/useMemory";

export default function Memory() {
  const { data, loading, toggle, edit, remove, clearAll } = useMemory();

  if (loading) return <EmptyText className="py-section">加载记忆…</EmptyText>;
  // 失败原因已用轻提示告知，这里只留一个可操作的空态
  if (!data) return <EmptyText className="py-section">记忆暂时取不到，请稍后刷新页面重试。</EmptyText>;

  return (
    <div className="space-y-gutter-lg">
      <PageHeader
        title="我的记忆"
        desc="跨会话保存的偏好、身份与背景；你可以随时修改或删除。"
        actions={
          <>
            <ActionLink onClick={toggle}>{data.enabled ? "关闭记忆" : "开启记忆"}</ActionLink>
            <ActionLink tone="danger" onClick={clearAll}>清空</ActionLink>
          </>
        }
      />

      {!data.enabled && (
        <p className="rounded border border-light-warning bg-light-warning-container px-gutter-md py-gutter-sm font-body text-body-sm text-light-on-warning-container dark:border-dark-warning dark:bg-dark-warning-container dark:text-dark-on-warning-container">
          记忆已关闭：不会提取新记忆，也不会注入已有记忆。
        </p>
      )}

      <section className="space-y-gutter-sm">
        <h3 className="font-headline text-title-md text-light-on-surface dark:text-dark-on-surface">卡片</h3>
        {data.cards.length === 0 ? (
          <EmptyText>暂无卡片记忆。</EmptyText>
        ) : (
          <div className="space-y-gutter-sm">
            {data.cards.map((item) => (
              <MemoryCard key={item.id} item={item} onEdit={edit} onRemove={remove} />
            ))}
          </div>
        )}
      </section>

      <section className="space-y-gutter-sm">
        <h3 className="font-headline text-title-md text-light-on-surface dark:text-dark-on-surface">笔记</h3>
        {data.notes.length === 0 ? (
          <EmptyText>暂无笔记记忆。</EmptyText>
        ) : (
          <div className="space-y-gutter-sm">
            {data.notes.map((item) => (
              <MemoryCard key={item.id} item={item} onEdit={edit} onRemove={remove} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}