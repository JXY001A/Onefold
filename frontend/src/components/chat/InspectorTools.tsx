import type { ToolRun } from "../../lib/chat";
import { clip, toolLabel, toolTarget } from "../../lib/tools";
import Icon from "../ui/Icon";

/** 检查器「工具」面板：一级为 mono 行（工具 · 目标 · 状态），二级展开保留真实网页清单。 */
export default function InspectorTools({ tools }: { tools: ToolRun[] }) {
  if (tools.length === 0) {
    return (
      <div className="flex flex-col items-center gap-gutter-sm px-gutter-md py-section text-center">
        <Icon name="travel_explore" size={28} className="text-light-outline dark:text-dark-outline" />
        <p className="font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">本轮还没有工具调用。发送问题后，联网搜索与读取的网页会列在这里。</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {tools.map((t) => {
        const items = t.data?.items ?? [];
        const fetched = t.data?.kind === "fetch" ? t.data : null;
        const status = t.status === "running" ? "运行中…" : t.status === "error" ? "未成功" : "已完成";
        const count = fetched ? 1 : items.length;
        return (
          <div key={t.id} className="border-b border-light-outline-variant last:border-0 dark:border-dark-outline-variant">
            <div className="flex items-center justify-between gap-gutter-sm py-1">
              <span className="min-w-0 truncate font-mono text-mono-sm text-light-on-surface dark:text-dark-on-surface">
                {toolLabel(t.name)} · {clip(toolTarget(t.args, t.data), 22)}
              </span>
              <span className={`shrink-0 font-mono text-mono-sm ${t.status === "error" ? "text-light-warning dark:text-dark-warning" : "text-light-primary dark:text-dark-primary"}`}>{status}</span>
            </div>

            {count > 0 && (
              <details className="group pb-2">
                <summary className="flex cursor-pointer list-none items-center gap-1 font-label text-label-sm text-light-outline [&::-webkit-details-marker]:hidden dark:text-dark-outline">
                  <Icon name="expand_more" size={14} className="transition-transform duration-state-change group-open:rotate-180" />
                  网页与正文（{count}）
                </summary>
                <div className="mt-1 flex flex-col gap-1 border-l border-light-outline-variant pl-gutter-sm dark:border-dark-outline-variant">
                  {fetched && (
                    <a href={fetched.url} target="_blank" rel="noreferrer" className="truncate font-label text-label-sm text-light-on-surface-variant hover:text-light-primary dark:text-dark-on-surface-variant dark:hover:text-dark-primary">
                      {fetched.title}
                    </a>
                  )}
                  {items.map((it, i) => (
                    <a key={it.url || `${i}-${it.title}`} href={it.url || undefined} target="_blank" rel="noreferrer" className="truncate font-label text-label-sm text-light-on-surface-variant hover:text-light-primary dark:text-dark-on-surface-variant dark:hover:text-dark-primary">
                      {it.title}
                    </a>
                  ))}
                </div>
              </details>
            )}
          </div>
        );
      })}
    </div>
  );
}
