import type { Doc } from "../../lib/documents";
import { ActionLink, EmptyText } from "../ui/kit";
import { TableShell, Td, Th, THead } from "../ui/table";

type Props = {
  docs: Doc[];
  scope: "personal" | "public";
  isAdmin: boolean;
  onDelete: (doc: Doc) => void;
  onCollect: (id: string) => void;
  onRetry: (doc: Doc) => void;
  onPublish: (id: string) => void;
};

/** 个人/公共文档共用表格；公共库对普通用户只读。 */
export default function DocTable({ docs, scope, isAdmin, onDelete, onCollect, onRetry, onPublish }: Props) {
  if (docs.length === 0) {
    return <EmptyText className="p-gutter-lg">{scope === "public" ? "公共知识库还没有文档。" : "还没有文档，先上传一个 PDF / MD / TXT。"}</EmptyText>;
  }

  return (
    <TableShell>
      <THead>
        <tr>
          <Th>文件名</Th>
          <Th>类型</Th>
          <Th>状态</Th>
          <Th>大小</Th>
          <Th className="text-right">操作</Th>
        </tr>
      </THead>
      <tbody>
        {docs.map((doc) => (
          <tr key={doc.id}>
            <Td>{doc.filename}</Td>
            <Td>{doc.scope === "public" ? "公共" : doc.kind}</Td>
            <Td>
              <div>{doc.status}</div>
              {doc.status === "ready" && (
                <div className="font-label text-label-sm text-light-outline dark:text-dark-outline">{doc.chunk_count} 块{doc.page_count ? ` · ${doc.page_count} 页` : ""}</div>
              )}
              {doc.error && <div className="max-w-[220px] truncate font-label text-label-sm text-light-error dark:text-dark-error" title={doc.error}>{doc.error}</div>}
            </Td>
            <Td className="font-mono text-mono-sm tabular-nums">{Math.round(doc.size / 1024)} KB</Td>
            <Td className="text-right">
              <div className="flex justify-end gap-gutter-sm">
                {doc.status === "failed" && (scope === "personal" || isAdmin) && <ActionLink tone="warning" onClick={() => onRetry(doc)}>重试</ActionLink>}
                {scope === "personal" && isAdmin && doc.status === "ready" && <ActionLink tone="primary" onClick={() => onPublish(doc.id)}>发布到公共</ActionLink>}
                {scope === "personal" && doc.kind === "temp" && <ActionLink onClick={() => onCollect(doc.id)}>收藏</ActionLink>}
                {(scope === "personal" || isAdmin) && <ActionLink tone="danger" onClick={() => onDelete(doc)}>删除</ActionLink>}
              </div>
            </Td>
          </tr>
        ))}
      </tbody>
    </TableShell>
  );
}