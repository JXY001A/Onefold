import type { ToolRun } from "../../lib/chat";
import { hitCount } from "../../lib/tools";

/** 右上角的胶囊：正在搜索 / 搜索到 N 个网页，点开看链接与简介 */
export default function ToolStatus({ tools, onClick }: { tools: ToolRun[]; onClick: () => void }) {
  const running = tools.some((t) => t.status === "running");
  const failed = tools.filter((t) => t.status === "error").length;
  const hits = tools.reduce((n, t) => n + hitCount(t.data), 0);

  let label = `已调用 ${tools.length} 次工具`;
  if (running) {
    label = "正在搜索";
  } else if (hits > 0) {
    label = `搜索到 ${hits} 个网页`;
  } else if (tools.length === 1) {
    label = "已调用 1 次工具";
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex shrink-0 items-center gap-1 rounded-full border px-2.5 py-1 text-xs transition ${
        running
          ? "border-blue-200 bg-blue-50 text-blue-600"
          : failed
            ? "border-slate-200 text-amber-600 hover:border-slate-300"
            : "border-slate-200 text-slate-500 hover:border-slate-300 hover:text-slate-700"
      }`}
      title="查看搜索与抓取的详细内容"
    >
      {running ? (
        <span className="inline-block h-3 w-3 animate-spin rounded-full border border-blue-400 border-t-transparent" />
      ) : (
        <svg viewBox="0 0 20 20" fill="none" className="h-3.5 w-3.5">
          <circle cx="9" cy="9" r="5.5" stroke="currentColor" strokeWidth="1.6" />
          <path d="M13.5 13.5 17 17" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      )}
      <span>{label}</span>
      {failed > 0 && !running && <span className="opacity-70">（{failed} 次未成功）</span>}
      <svg viewBox="0 0 20 20" fill="none" className="h-3 w-3 opacity-60">
        <path d="m5 8 5 5 5-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    </button>
  );
}
