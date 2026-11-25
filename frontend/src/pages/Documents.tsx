import type { ChangeEvent } from "react";
import DocTable from "../components/documents/DocTable";
import Icon from "../components/ui/Icon";
import { EmptyText, PageHeader, PillTabs } from "../components/ui/kit";
import { useAuth } from "../context/AuthContext";
import { useDocuments } from "../hooks/useDocuments";
import { canUseAdmin } from "../lib/roles";

const TABS = [
  { key: "personal", label: "个人知识库" },
  { key: "public", label: "公共知识库" },
] as const;

export default function Documents() {
  const { me } = useAuth();
  const isAdmin = canUseAdmin(me?.role);
  const { scope, setScope, docs, upload, remove, collect, retry, publish } = useDocuments();

  const pick = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) void upload(file, scope);
    // 清空选择：同一个文件再次上传也能触发 change
    event.target.value = "";
  };

  const canUpload = scope === "personal" || isAdmin;

  return (
    <div className="space-y-gutter-md">
      <PageHeader
        title="知识库"
        desc="个人知识库可自由上传；公共知识库由管理员维护，普通用户只读。"
        actions={
          canUpload ? (
            <label className="inline-flex cursor-pointer items-center gap-1.5 rounded border border-light-outline-variant px-gutter-md py-2 font-label text-label-md text-light-on-surface transition-colors hover:bg-light-surface-container-high dark:border-dark-outline-variant dark:text-dark-on-surface dark:hover:bg-dark-surface-container-high">
              <Icon name="upload_file" size={16} />
              {scope === "public" ? "上传公共文档" : "上传个人文档"}
              <input type="file" className="hidden" onChange={pick} />
            </label>
          ) : undefined
        }
      />

      <PillTabs tabs={TABS.map((t) => ({ key: t.key, label: t.label }))} active={scope} onChange={(k) => setScope(k as "personal" | "public")} />

      {scope === "public" && !isAdmin && <EmptyText>公共知识库由管理员维护，普通用户只读。</EmptyText>}

      <DocTable docs={docs} scope={scope} isAdmin={isAdmin} onDelete={remove} onCollect={collect} onRetry={retry} onPublish={publish} />
    </div>
  );
}