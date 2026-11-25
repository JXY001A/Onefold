import type { Doc } from "../../lib/documents";
import { formatSize, scopeLabel, statusLabel, statusTone } from "../../lib/docDisplay";
import { Badge, EmptyText } from "../ui/kit";

type Props = {
  docs: Doc[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  isAdmin: boolean;
  busy: boolean;
  onDelete: (doc: Doc) => void;
  onRetry: (doc: Doc) => void;
  onPublish: (id: string) => void;
  emptyText: string;
};

/** 2.0 文档列表：白底卡片行 + 真实字段；星标/收藏按决议不实现。 */
export default function DocList({ docs, selectedId, onSelect, isAdmin, busy, onDelete, onRetry, onPublish, emptyText }: Props) {
  if (docs.length === 0) return <EmptyText className="py-section text-center">{emptyText}</EmptyText>;

  return (
    <div className="overflow-hidden rounded border border-light-outline-variant bg-light-surface dark:border-dark-outline-variant dark:bg-dark-surface">
      {docs.map((doc) => {
        const personal = doc.scope === "personal";
        const canDelete = doc.scope !== "public" || isAdmin;
        const canRetry = doc.status === "failed" && (doc.scope !== "public" || isAdmin);
        const canPublish = personal && isAdmin && doc.status === "ready";
        const active = doc.id === selectedId;
        const meta = [formatSize(doc.size)];
        if (doc.status === "ready") {
          meta.push(`${doc.chunk_count} 块`);
          if (doc.page_count) meta.push(`${doc.page_count} 页`);
        }

        return (
          <div
            key={doc.id}
            role="button"
            tabIndex={0}
            onClick={() => onSelect(doc.id)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelect(doc.id);
              }
            }}
            className={`flex cursor-pointer flex-wrap items-center justify-between gap-gutter-sm border-b border-light-outline-variant px-gutter-md py-gutter-sm last:border-0 dark:border-dark-outline-variant ${
              active ? "bg-light-surface-container dark:bg-dark-surface-container" : "hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container-low"
            }`}
          >
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <div className="flex min-w-0 items-center gap-2">
                <span className="truncate font-label text-label-md text-light-on-surface dark:text-dark-on-surface">{doc.filename}</span>
                <Badge>{scopeLabel(doc.scope)}</Badge>
              </div>
              <span className="font-mono text-mono-sm tabular-nums text-light-outline dark:text-dark-outline">
                {meta.join(" · ")}
              </span>
              {doc.error && <span className="max-w-[420px] truncate font-label text-label-sm text-light-error dark:text-dark-error" title={doc.error}>{doc.error}</span>}
            </div>

            <div className="flex shrink-0 flex-col items-end gap-1">
              <span className={`inline-flex items-center gap-1 font-mono text-mono-sm ${statusTone(doc.status)}`}>
                <span className={`h-1.5 w-1.5 rounded-full ${doc.status === "ready" ? "bg-light-primary dark:bg-dark-primary" : doc.status === "failed" ? "bg-light-error dark:bg-dark-error" : "bg-light-warning dark:bg-dark-warning"}`} />
                {statusLabel(doc.status)}
              </span>
              <div className="flex items-center gap-gutter-sm">
                {canRetry && <Action label="重试" tone="text-light-warning dark:text-dark-warning" disabled={busy} onClick={() => onRetry(doc)} />}
                {canPublish && <Action label="发布到公共" tone="text-light-primary dark:text-dark-primary" disabled={busy} onClick={() => onPublish(doc.id)} />}
                {canDelete && <Action label="删除" tone="text-light-error dark:text-dark-error" disabled={busy} onClick={() => onDelete(doc)} />}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Action({ label, tone, disabled, onClick }: { label: string; tone: string; disabled: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className={`underline underline-offset-2 font-label text-label-sm disabled:opacity-40 ${tone}`}
    >
      {label}
    </button>
  );
}
