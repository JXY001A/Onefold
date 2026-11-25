import type { ToolRun } from "../../lib/chat";
import { hitCount } from "../../lib/tools";
import Icon from "../ui/Icon";

/** 消息右上角胶囊：正在搜索 / 搜索到 N 个网页，点开看链接与简介。 */
export default function ToolStatus({ tools, onClick }: { tools: ToolRun[]; onClick: () => void }) {
  const running = tools.some((t) => t.status === "running");
  const failed = tools.filter((t) => t.status === "error").length;
  const hits = tools.reduce((n, t) => n + hitCount(t.data), 0);

  let label = `已调用 ${tools.length} 次工具`;
  if (running) label = "正在搜索";
  else if (hits > 0) label = `搜索到 ${hits} 个网页`;
  else if (tools.length === 1) label = "已调用 1 次工具";

  const tone = running
    ? "border-light-primary text-light-primary dark:border-dark-primary dark:text-dark-primary"
    : failed
      ? "border-light-warning text-light-warning dark:border-dark-warning dark:text-dark-warning"
      : "border-light-outline-variant text-light-on-surface-variant dark:border-dark-outline-variant dark:text-dark-on-surface-variant";

  return (
    <button
      type="button"
      onClick={onClick}
      title="查看搜索与抓取的详细内容"
      className={`flex shrink-0 items-center gap-1 rounded-full border bg-light-surface px-2.5 py-1 font-label text-label-sm transition-colors duration-state-change hover:bg-light-surface-container dark:bg-dark-surface dark:hover:bg-dark-surface-container ${tone}`}
    >
      {running ? (
        <span className="inline-block h-3 w-3 animate-spin rounded-full border border-current border-t-transparent" />
      ) : (
        <Icon name="travel_explore" size={14} />
      )}
      <span>{label}</span>
      {failed > 0 && !running && <span className="opacity-70">（{failed} 次未成功）</span>}
      <Icon name="expand_more" size={14} />
    </button>
  );
}