import type { ToolRun } from "../../lib/chat";
import { clip, hitCount, toolLabel, toolTarget } from "../../lib/tools";
import Icon from "../ui/Icon";

type Props = {
  tools: ToolRun[];
  /** 打开抓取详情抽屉（业务入口保留） */
  onOpenDetails?: () => void;
};

/** 检索状态卡：圆点 + 真实工具统计 + 双列明细；耗时数据缺失，不显示。 */
export default function RetrievalStatus({ tools, onOpenDetails }: Props) {
  if (tools.length === 0) return null;
  const running = tools.some((t) => t.status === "running");
  const hits = tools.reduce((n, t) => n + hitCount(t.data), 0);

  return (
    <details open className="group rounded border border-light-outline-variant bg-light-surface dark:border-dark-outline-variant dark:bg-dark-surface">
      <summary className="flex cursor-pointer list-none items-center gap-gutter-sm px-gutter-md py-2 [&::-webkit-details-marker]:hidden">
        <span className={`h-2 w-2 shrink-0 rounded-full ${running ? "animate-pulse bg-light-warning dark:bg-dark-warning" : "bg-light-primary dark:bg-dark-primary"}`} />
        <span className="flex-1 font-label text-label-md text-light-on-surface dark:text-dark-on-surface">
          {running ? "正在检索与读取…" : `${tools.length} 次工具调用`}
          {hits > 0 && <span className="font-mono text-mono-sm font-normal tabular-nums text-light-outline dark:text-dark-outline"> · {hits} 个网页</span>}
        </span>
        <Icon name="expand_more" size={16} className="text-light-outline transition-transform duration-state-change group-open:rotate-180 dark:text-dark-outline" />
      </summary>

      <div className="mt-2 grid grid-cols-1 gap-gutter-sm border-t border-light-outline-variant px-gutter-md py-2 sm:grid-cols-2 dark:border-dark-outline-variant">
        {tools.map((t) => (
          <div key={t.id} className="flex items-center gap-1.5 font-label text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
            <Icon
              name={t.status === "running" ? "progress_activity" : t.status === "error" ? "error" : "check_circle"}
              size={14}
              className={t.status === "error" ? "text-light-warning dark:text-dark-warning" : "text-light-primary dark:text-dark-primary"}
            />
            <span className="shrink-0 text-light-on-surface dark:text-dark-on-surface">{toolLabel(t.name)}</span>
            <span className="min-w-0 truncate font-mono text-mono-sm text-light-outline dark:text-dark-outline">{clip(toolTarget(t.args, t.data), 28)}</span>
          </div>
        ))}
        {onOpenDetails && (
          <button type="button" onClick={onOpenDetails} className="justify-self-start font-label text-label-sm text-light-primary underline underline-offset-2 dark:text-dark-primary">
            查看抓取详情
          </button>
        )}
      </div>
    </details>
  );
}
