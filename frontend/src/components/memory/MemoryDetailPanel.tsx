import type { MemoryItem } from "../../lib/memory";
import { bucketOf } from "../../lib/memoryCategories";
import { kindLabel, memoryDateTime } from "../../lib/memoryDisplay";
import { mockCitationLogs, mockCitations, mockLastCitedAt } from "../../lib/memoryMock";
import { useToast } from "../../context/ToastContext";
import Icon from "../ui/Icon";

/** mock 字段的「示例」微标。 */
function MockTag() {
  return <span className="font-mono text-[10px] text-dark-outline">示例</span>;
}

type Props = {
  item: MemoryItem;
  effectiveActive: boolean;
  onEdit: () => void;
  onDelete: () => void;
};

/** 记忆详情面板：属性网格 + 引用记录 + 底部操作。
 * 引用数据为 mock（带示例微标）；来源显示真实 run 记录 id。 */
export default function MemoryDetailPanel({ item, effectiveActive, onEdit, onDelete }: Props) {
  const toast = useToast();
  const citations = mockCitations(item.id);
  const lastCited = mockLastCitedAt(item.id);
  const logs = mockCitationLogs(item.id);

  return (
    <aside
      aria-label="记忆详情"
      className="flex flex-col rounded border border-dark-outline-variant bg-dark-surface lg:sticky lg:top-gutter-lg"
    >
      <div className="flex items-center justify-between gap-gutter-sm border-b border-dark-outline-variant px-gutter-lg py-gutter-md">
        <h2 className="font-title text-title-md text-dark-on-surface">记忆详情</h2>
        <div className="flex items-center gap-gutter-xs">
          <button
            type="button"
            onClick={onEdit}
            className="inline-flex items-center gap-1 rounded-sm bg-dark-surface-container px-2.5 py-1 font-label text-label-sm text-dark-on-surface-variant transition-colors hover:bg-dark-surface-container-high hover:text-dark-on-surface"
          >
            <Icon name="edit" size={15} />
            编辑
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="inline-flex items-center gap-1 rounded-sm bg-dark-surface-container px-2.5 py-1 font-label text-label-sm text-dark-error transition-colors hover:bg-dark-surface-container-high"
          >
            <Icon name="delete" size={15} />
            删除
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-gutter-md p-gutter-lg">
        <div className="flex flex-col gap-gutter-xs rounded border border-dark-outline-variant bg-dark-surface-container-low p-gutter-md">
          <span className="font-label text-label-sm text-dark-outline">记忆内容</span>
          <p className="font-body text-body-md text-dark-on-surface">{item.text}</p>
        </div>

        <div className="grid grid-cols-2 gap-x-gutter-md gap-y-gutter-sm border-y border-dark-outline-variant py-gutter-sm">
          <div className="flex flex-col gap-0.5">
            <span className="font-label text-label-sm text-dark-outline">分类</span>
            <span className="font-label text-label-md text-dark-on-surface">{bucketOf(item.category)}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="font-label text-label-sm text-dark-outline">记忆类型</span>
            <span className="font-label text-label-md text-dark-on-surface">{kindLabel(item.kind)}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="font-label text-label-sm text-dark-outline">激活状态</span>
            <span
              className={`flex items-center gap-1 font-label text-label-sm ${
                effectiveActive ? "text-dark-success" : "text-dark-outline"
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${effectiveActive ? "bg-dark-success" : "bg-dark-outline"}`} />
              {effectiveActive ? "已激活" : "已停用"}
              <MockTag />
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="font-label text-label-sm text-dark-outline">被 AI 引用次数</span>
            <span className="flex items-center gap-1 font-mono text-mono-sm tabular-nums text-dark-primary">
              {citations} 次 <MockTag />
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="font-label text-label-sm text-dark-outline">创建时间</span>
            <span className="font-mono text-mono-sm tabular-nums text-dark-on-surface-variant">
              {memoryDateTime(item.happened_at)}
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="font-label text-label-sm text-dark-outline">最后更新时间</span>
            <span className="font-mono text-mono-sm tabular-nums text-dark-on-surface-variant">
              {memoryDateTime(item.updated_at)}
            </span>
          </div>
          <div className="col-span-2 flex flex-col gap-0.5">
            <span className="font-label text-label-sm text-dark-outline">最近一次引用时间</span>
            <span className="flex items-center gap-1 font-mono text-mono-sm tabular-nums text-dark-on-surface-variant">
              {lastCited || "暂无引用"}
              {lastCited && <MockTag />}
            </span>
          </div>
          <div className="col-span-2 flex flex-col gap-0.5">
            <span className="font-label text-label-sm text-dark-outline">记忆来源</span>
            <span className="font-body text-body-sm text-dark-on-surface-variant">
              {item.source_run_id ? `来自研究对话（记录 ${item.source_run_id.slice(0, 8)}）` : "无关联会话"}
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-gutter-sm">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1 font-label text-label-md text-dark-on-surface">
              引用记录 <MockTag />
            </span>
            <span className="font-mono text-mono-sm tabular-nums text-dark-outline">共 {citations} 次</span>
          </div>
          {logs.length > 0 ? (
            logs.map((log, i) => (
              <div
                key={i}
                className="flex items-center justify-between gap-gutter-sm rounded border border-dark-outline-variant bg-dark-surface-container-low px-gutter-sm py-gutter-xs"
              >
                <div className="flex min-w-0 flex-col">
                  <span className="truncate font-body text-body-sm text-dark-on-surface">{log.session}</span>
                  <span className="font-mono text-mono-sm tabular-nums text-dark-outline">{log.time}</span>
                </div>
                <button
                  type="button"
                  onClick={() => toast.push("success", "查看来源对话功能敬请期待")}
                  className="shrink-0 font-label text-label-sm text-dark-primary hover:underline"
                >
                  查看来源对话
                </button>
              </div>
            ))
          ) : (
            <div className="rounded border border-dark-outline-variant bg-dark-surface-container-low px-gutter-md py-gutter-md text-center">
              <span className="font-body text-body-sm text-dark-outline">暂无详细引用记录</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between gap-gutter-sm rounded-b border-t border-dark-outline-variant bg-dark-surface-container-low px-gutter-lg py-gutter-md">
        <button
          type="button"
          onClick={onDelete}
          className="inline-flex items-center gap-gutter-xs rounded border border-dark-outline-variant bg-dark-surface px-gutter-md py-1.5 font-label text-label-md text-dark-error transition-colors hover:bg-dark-surface-container"
        >
          删除记忆
        </button>
        <button
          type="button"
          onClick={onEdit}
          className="inline-flex items-center gap-gutter-xs rounded bg-dark-primary px-gutter-md py-1.5 font-label text-label-md text-dark-on-primary transition-opacity hover:opacity-90"
        >
          编辑记忆
        </button>
      </div>
    </aside>
  );
}
