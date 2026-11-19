import { useEffect } from "react";

import type { ToolRun } from "../../lib/chat";
import { clip, toolLabel, toolTarget } from "../../lib/tools";

/** 一条工具调用：搜索列命中，抓取列页面本身 */
function Group({ tool }: { tool: ToolRun }) {
  const target = clip(toolTarget(tool.args, tool.data), 40);
  const data = tool.data;
  const items = data?.items ?? [];

  return (
    <section>
      <div className="mb-2 flex items-baseline gap-1.5 text-xs">
        <span className="shrink-0 font-medium text-slate-700">{toolLabel(tool.name)}</span>
        {target && <span className="min-w-0 truncate text-slate-400">「{target}」</span>}
        {tool.status === "error" && (
          <span className="shrink-0 text-amber-600">{tool.summary || "未成功"}</span>
        )}
      </div>

      {data?.kind === "fetch" && (
        <a
          href={data.url}
          target="_blank"
          rel="noreferrer"
          className="block rounded-lg border border-slate-100 p-3 transition hover:border-slate-300 hover:bg-slate-50"
        >
          <div className="text-sm font-medium leading-5 text-slate-800">{data.title}</div>
          <div className="mt-1 truncate text-xs text-slate-400">
            {data.url} · {data.chars ?? 0} 字
          </div>
          {data.snippet && (
            <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">{data.snippet}</p>
          )}
        </a>
      )}

      {items.map((it, i) => (
        <a
          key={it.url || `${i}-${it.title}`}
          href={it.url || undefined}
          target="_blank"
          rel="noreferrer"
          className="mt-2 block rounded-lg border border-slate-100 p-3 transition hover:border-slate-300 hover:bg-slate-50"
        >
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded bg-slate-100 text-[10px] text-slate-500">
              {(it.site || "网").slice(0, 1)}
            </span>
            <span className="truncate">{it.site || "来源"}</span>
            {it.date && <span className="shrink-0">· {it.date}</span>}
          </div>
          <div className="mt-1 text-sm font-medium leading-5 text-slate-800">{it.title}</div>
          {it.snippet && (
            <p className="mt-1 line-clamp-3 text-xs leading-5 text-slate-500">{it.snippet}</p>
          )}
        </a>
      ))}

      {data?.kind !== "fetch" && items.length === 0 && (
        <p className="text-xs text-slate-400">
          {tool.status === "running" ? "搜索中…" : tool.summary || "没有可展示的结果"}
        </p>
      )}
    </section>
  );
}

/** 右侧抽屉：列出本轮所有搜索与抓取的链接和简介 */
export default function ToolDrawer({ tools, onClose }: { tools: ToolRun[]; onClose: () => void }) {
  // Esc 关闭 + 打开期间锁住背景滚动
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
      <div className="absolute inset-0 bg-slate-900/25" onClick={onClose} />
      <aside className="absolute inset-y-0 right-0 flex w-full max-w-md flex-col border-l border-slate-200 bg-white shadow-2xl">
        <header className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
          <h2 className="text-sm font-medium text-slate-700">搜索与抓取</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            aria-label="关闭"
          >
            ✕
          </button>
        </header>
        <div className="flex-1 space-y-5 overflow-y-auto px-4 py-4">
          {tools.map((t) => (
            <Group key={t.id} tool={t} />
          ))}
        </div>
      </aside>
    </div>
  );
}
