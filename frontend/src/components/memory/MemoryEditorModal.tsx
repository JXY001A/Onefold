import { useState, type FormEvent } from "react";
import type { MemoryItem } from "../../lib/memory";
import { bucketOf, CATEGORY_BUCKETS } from "../../lib/memoryCategories";
import { kindLabel } from "../../lib/memoryDisplay";
import Icon from "../ui/Icon";

type Props = {
  item: MemoryItem;
  effectiveActive: boolean;
  onClose: () => void;
  onSave: (text: string) => Promise<boolean>;
};

/** 编辑记忆弹窗：仅「记忆内容」可改并真实保存（PATCH text）；
 * 分类/类型/激活状态后端暂不支持修改，按口径只读展示。 */
export default function MemoryEditorModal({ item, effectiveActive, onClose, onSave }: Props) {
  const [text, setText] = useState(item.text);
  const [saving, setSaving] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const next = text.trim();
    if (!next || saving) return;
    setSaving(true);
    const ok = await onSave(next);
    setSaving(false);
    if (ok) onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-dark-background/80 px-gutter-md"
      role="dialog"
      aria-modal="true"
      aria-labelledby="memory-editor-title"
    >
      <div className="w-full max-w-[540px] overflow-hidden rounded-lg border border-dark-outline-variant bg-dark-surface">
        <div className="flex items-center justify-between border-b border-dark-outline-variant px-gutter-lg py-gutter-md">
          <h3 id="memory-editor-title" className="font-headline text-headline-md text-dark-on-surface">
            编辑记忆
          </h3>
          <button
            type="button"
            aria-label="关闭弹窗"
            onClick={onClose}
            className="rounded-sm p-1 text-dark-on-surface-variant hover:bg-dark-surface-container hover:text-dark-on-surface"
          >
            <Icon name="close" size={18} />
          </button>
        </div>

        <form onSubmit={submit} className="flex flex-col gap-gutter-md p-gutter-lg">
          <div className="flex flex-col gap-gutter-xs">
            <label htmlFor="memory-editor-content" className="font-label text-label-md text-dark-on-surface">
              记忆内容
            </label>
            <textarea
              id="memory-editor-content"
              rows={4}
              required
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="例如：研究报告中所有指标需附带来源文件名与页码，优先使用中文学术术语。"
              className="w-full rounded border border-dark-outline-variant bg-dark-surface-container-low p-3 font-body text-body-sm text-dark-on-surface placeholder:text-dark-outline focus:border-dark-primary focus:ring-0"
            />
          </div>

          <div className="grid grid-cols-1 gap-gutter-md sm:grid-cols-2">
            <div className="flex flex-col gap-gutter-xs">
              <label htmlFor="memory-editor-category" className="font-label text-label-md text-dark-on-surface">
                记忆分类
              </label>
              <select
                id="memory-editor-category"
                value={bucketOf(item.category)}
                disabled
                title="当前版本暂不支持修改分类"
                className="w-full rounded border border-dark-outline-variant bg-dark-surface-container-low px-3 py-2 font-label text-label-md text-dark-on-surface opacity-70"
              >
                {CATEGORY_BUCKETS.map((b) => (
                  <option key={b.label} value={b.label}>
                    {b.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-gutter-xs">
              <span className="font-label text-label-md text-dark-on-surface">记忆类型</span>
              <div className="grid grid-cols-2 gap-gutter-xs rounded border border-dark-outline-variant bg-dark-surface-container-low p-1">
                {(["note", "card"] as const).map((kind) => (
                  <span
                    key={kind}
                    aria-disabled="true"
                    title="当前版本暂不支持修改类型"
                    className={`rounded-sm py-1.5 text-center font-label text-label-sm ${
                      item.kind === kind
                        ? "bg-dark-primary-container text-dark-on-primary-container"
                        : "text-dark-outline"
                    }`}
                  >
                    {kindLabel(kind)}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between rounded border border-dark-outline-variant bg-dark-surface-container-low px-gutter-md py-gutter-sm">
            <div className="flex flex-col">
              <span className="font-label text-label-md text-dark-on-surface">是否激活</span>
              <span className="font-label text-label-sm text-dark-on-surface-variant">
                开启后将在全局记忆启用时参与 AI 上下文（当前版本暂不支持修改）
              </span>
            </div>
            <span
              aria-disabled="true"
              className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full opacity-70 ${
                effectiveActive ? "bg-dark-success" : "bg-dark-surface-container-highest"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-3.5 w-3.5 rounded-full ${
                  effectiveActive ? "translate-x-[18px] bg-dark-on-success" : "translate-x-[3px] bg-dark-on-surface-variant"
                }`}
              />
            </span>
          </div>

          <div className="flex items-center justify-end gap-gutter-sm border-t border-dark-outline-variant pt-gutter-sm">
            <button
              type="button"
              onClick={onClose}
              className="rounded bg-dark-surface-container px-gutter-md py-2 font-label text-label-md text-dark-on-surface-variant hover:text-dark-on-surface"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={!text.trim() || saving}
              className="rounded bg-dark-primary px-gutter-md py-2 font-label text-label-md text-dark-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving ? "保存中…" : "保存记忆"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
