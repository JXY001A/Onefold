import { useMemo, useState } from "react";
import DocInspector from "../components/documents/DocInspector";
import DocList from "../components/documents/DocList";
import DocUpload, { UploadButton } from "../components/documents/DocUpload";
import PageWorkspace from "../components/pages/PageWorkspace";
import { PageHeader, Tabs } from "../components/ui/kit";
import { useAuth } from "../context/AuthContext";
import { useDocuments } from "../hooks/useDocuments";
import { canUseAdmin } from "../lib/roles";

type Scope = "all" | "public" | "personal";

/** 知识库（2.0 视觉壳 + 真实数据）：临时文档与收藏按决议省略。 */
export default function Documents() {
  const { me } = useAuth();
  const isAdmin = canUseAdmin(me?.role);
  const { personalDocs, publicDocs, upload, remove, retry, publish } = useDocuments();
  const [scope, setScope] = useState<Scope>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const all = useMemo(() => [...personalDocs, ...publicDocs], [personalDocs, publicDocs]);
  const visible = scope === "public" ? publicDocs : scope === "personal" ? personalDocs : all;
  const activeId = visible.some((d) => d.id === selectedId) ? selectedId : visible[0]?.id ?? null;
  const selected = visible.find((d) => d.id === activeId) ?? null;
  const canUpload = scope !== "public" || isAdmin;

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await fn();
    } finally {
      setBusy(false);
    }
  };

  const onFile = (file: File) => void run(() => upload(file, "personal"));

  const tabs = [
    { key: "all", label: `全部文档 · ${all.length}` },
    { key: "public", label: `公共知识库 · ${publicDocs.length}` },
    { key: "personal", label: `个人 / 临时 · ${personalDocs.length}` },
  ];

  const emptyText =
    scope === "public"
      ? "公共知识库还没有文档。"
      : scope === "personal"
        ? "还没有个人或临时文档，上传一篇 PDF / Markdown / TXT。"
        : "还没有文档，上传一篇 PDF / Markdown / TXT。";

  return (
    <PageWorkspace aside={<DocInspector doc={selected} />}>
      <div className="flex flex-col gap-gutter-lg">
        <PageHeader
          title="知识库"
          desc="公共知识库默认只读（管理员发布）；个人文档支持上传后自动解析与向量化。"
          actions={canUpload ? <UploadButton onFile={onFile} disabled={busy} primary /> : undefined}
        />

        {canUpload && <DocUpload onFile={onFile} disabled={busy} />}

        <Tabs tabs={tabs} active={scope} onChange={(k) => setScope(k as Scope)} />

        <DocList
          docs={visible}
          selectedId={activeId}
          onSelect={setSelectedId}
          isAdmin={isAdmin}
          busy={busy}
          onDelete={(doc) => void run(() => remove(doc))}
          onRetry={(doc) => void run(() => retry(doc))}
          onPublish={(id) => void run(() => publish(id))}
          emptyText={emptyText}
        />
      </div>
    </PageWorkspace>
  );
}
