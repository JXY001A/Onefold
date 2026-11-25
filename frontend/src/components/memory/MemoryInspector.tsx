import type { MemoryItem } from "../../lib/memory";
import { kindLabel, memoryDate } from "../../lib/memoryDisplay";
import { Badge } from "../ui/kit";

/** 2.0 记忆检查器：只展示真实字段；来源会话/作用范围等缺失项明确省略。 */
export default function MemoryInspector({ item, memoryEnabled }: { item: MemoryItem | null; memoryEnabled: boolean }) {
  return (
    <div className="flex flex-col gap-gutter-md p-gutter-md">
      <h2 className="font-label text-label-sm text-light-outline dark:text-dark-outline">选中记忆</h2>

      {!item ? (
        <p className="font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">选择一条记忆，查看分类、状态与更新时间。</p>
      ) : (
        <>
          <div className="flex flex-col gap-2">
            <h3 className="break-all font-headline text-title-md text-light-on-surface dark:text-dark-on-surface">
              {item.category ?? "其他"} · {item.key ?? "记忆"}
            </h3>
            <p className={`font-label text-label-sm ${memoryEnabled ? "text-light-primary dark:text-dark-primary" : "text-light-on-surface-variant dark:text-dark-on-surface-variant"}`}>
              {memoryEnabled ? "已启用" : "已停用"} · 提到 {item.mention_count} 次
            </p>
          </div>

          <section className="flex flex-col gap-2 border-t border-light-outline-variant pt-gutter-md dark:border-dark-outline-variant">
            <div className="flex items-center justify-between gap-gutter-sm">
              <span className="font-label text-label-sm text-light-outline dark:text-dark-outline">类型</span>
              <Badge>{kindLabel(item.kind)}</Badge>
            </div>
            <div className="flex items-center justify-between gap-gutter-sm">
              <span className="font-label text-label-sm text-light-outline dark:text-dark-outline">更新时间</span>
              <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">{memoryDate(item.updated_at)}</span>
            </div>
          </section>

          <p className="border-t border-light-outline-variant pt-gutter-md font-label text-label-sm text-light-outline dark:border-dark-outline-variant dark:text-dark-outline">
            提取来源会话与作用范围随后开放。
          </p>
        </>
      )}
    </div>
  );
}
