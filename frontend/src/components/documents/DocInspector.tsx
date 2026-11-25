import type { Doc } from "../../lib/documents";
import { formatSize, scopeLabel, statusLabel } from "../../lib/docDisplay";
import { Badge } from "../ui/kit";

/** 2.0 右检查器：仅展示真实文档字段；索引策略与权限为静态说明。 */
export default function DocInspector({ doc }: { doc: Doc | null }) {
  return (
    <div className="flex flex-col gap-gutter-md p-gutter-md">
      <h2 className="font-label text-label-sm text-light-outline dark:text-dark-outline">选中文档</h2>

      {!doc ? (
        <p className="font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">选择左侧一篇文档，查看作用域与索引状态。</p>
      ) : (
        <>
          <div className="flex flex-col gap-2">
            <div className="flex items-start justify-between gap-gutter-sm">
              <h3 className="min-w-0 truncate font-headline text-title-md text-light-on-surface dark:text-dark-on-surface" title={doc.filename}>{doc.filename}</h3>
              <Badge>{scopeLabel(doc.scope)}</Badge>
            </div>
            <p className="font-mono text-mono-sm tabular-nums text-light-outline dark:text-dark-outline">
              {formatSize(doc.size)}
              {doc.status === "ready" ? ` · ${doc.chunk_count} 块` : ""}
              {doc.page_count ? ` · ${doc.page_count} 页` : ""}
            </p>
            {doc.error && <p className="font-label text-label-sm text-light-error dark:text-dark-error">{doc.error}</p>}
          </div>

          <section className="flex flex-col gap-2 border-t border-light-outline-variant pt-gutter-md dark:border-dark-outline-variant">
            <h3 className="font-label text-label-sm text-light-outline dark:text-dark-outline">索引管线状态</h3>
            <p className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">上传 → 解析 → Embedding → Ready</p>
            <p className="font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
              当前状态：{statusLabel(doc.status)}
              {doc.status === "ready" ? `，已生成 ${doc.chunk_count} 个片段。` : "。"}
            </p>
          </section>

          <section className="flex flex-col gap-2 border-t border-light-outline-variant pt-gutter-md dark:border-dark-outline-variant">
            <h3 className="font-label text-label-sm text-light-outline dark:text-dark-outline">权限说明</h3>
            <p className="font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
              {doc.scope === "public"
                ? "公共知识库文档由管理员统一上传与发布，研究者仅可检索与引用，不可修改或删除。"
                : "个人文档仅自己可见，可随时删除；发布到公共后由管理员维护。"}
            </p>
          </section>
        </>
      )}
    </div>
  );
}
