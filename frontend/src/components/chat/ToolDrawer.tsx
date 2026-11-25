import { useEffect } from "react";
import type { ToolRun } from "../../lib/chat";
import { clip, toolLabel, toolTarget } from "../../lib/tools";
import Icon from "../ui/Icon";

/** 一条工具调用：搜索列命中，抓取列页面本身。 */
function Group({ tool }: { tool: ToolRun }) {
  const target = clip(toolTarget(tool.args, tool.data), 40);
  const data = tool.data;
  const items = data?.items ?? [];
  const card =
    "block rounded border border-light-outline-variant p-3 transition-colors duration-state-change hover:border-light-outline hover:bg-light-surface-container dark:border-dark-outline-variant dark:hover:border-dark-outline dark:hover:bg-dark-surface-container";

  return (
    <section>
      <div className="mb-2 flex items-baseline gap-1.5 font-label text-label-sm">
        <span className="shrink-0 font-medium text-light-on-surface dark:text-dark-on-surface">{toolLabel(tool.name)}</span>
        {target && <span className="min-w-0 truncate text-light-outline dark:text-dark-outline">「{target}」</span>}
        {tool.status === "error" && <span className="shrink-0 text-light-warning dark:text-dark-warning">{tool.summary || "未成功"}</span>}
      </div>

      {data?.kind === "fetch" && (
        <a href={data.url} target="_blank" rel="noreferrer" className={card}>
          <div className="font-label text-label-lg text-light-on-surface dark:text-dark-on-surface">{data.title}</div>
          <div className="mt-1 truncate font-mono text-mono-sm text-light-outline dark:text-dark-outline">{data.url} · {data.chars ?? 0} 字</div>
          {data.snippet && <p className="mt-2 line-clamp-2 font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">{data.snippet}</p>}
        </a>
      )}

      {items.map((it, i) => (
        <a key={it.url || `${i}-${it.title}`} href={it.url || undefined} target="_blank" rel="noreferrer" className={`mt-2 ${card}`}>
          <div className="flex items-center gap-1.5 font-label text-label-sm text-light-outline dark:text-dark-outline">
            <span className="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-sm bg-light-surface-container-high text-[10px] text-light-on-surface-variant dark:bg-dark-surface-container-high dark:text-dark-on-surface-variant">{(it.site || "网").slice(0, 1)}</span>
            <span className="truncate">{it.site || "来源"}</span>
            {it.date && <span className="shrink-0">· {it.date}</span>}
          </div>
          <div className="mt-1 font-label text-label-lg text-light-on-surface dark:text-dark-on-surface">{it.title}</div>
          {it.snippet && <p className="mt-1 line-clamp-3 font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">{it.snippet}</p>}
        </a>
      ))}

      {data?.kind !== "fetch" && items.length === 0 && (
        <p className="font-label text-label-sm text-light-outline dark:text-dark-outline">{tool.status === "running" ? "搜索中…" : tool.summary || "没有可展示的结果"}</p>
      )}
    </section>
  );
}

/** 右侧抽屉：列出本轮所有搜索与抓取的链接和简介。 */
export default function ToolDrawer({ tools, onClose }: { tools: ToolRun[]; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <aside className="absolute inset-y-0 right-0 flex w-full max-w-md flex-col border-l border-light-outline-variant bg-light-surface shadow-2xl dark:border-dark-outline-variant dark:bg-dark-surface">
        <header className="flex items-center justify-between border-b border-light-outline-variant px-gutter-md py-gutter-sm dark:border-dark-outline-variant">
          <h2 className="font-headline text-title-md text-light-on-surface dark:text-dark-on-surface">搜索与抓取</h2>
          <button type="button" onClick={onClose} aria-label="关闭" className="rounded p-1 text-light-on-surface-variant hover:bg-light-surface-container-high dark:text-dark-on-surface-variant dark:hover:bg-dark-surface-container-high">
            <Icon name="close" size={18} />
          </button>
        </header>
        <div className="flex-1 space-y-5 overflow-y-auto px-gutter-md py-gutter-md">
          {tools.map((t) => (
            <Group key={t.id} tool={t} />
          ))}
        </div>
      </aside>
    </div>
  );
}