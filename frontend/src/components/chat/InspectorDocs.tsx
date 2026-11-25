import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchPersonalDocs, fetchPublicDocs, type Doc } from "../../lib/documents";
import { ensureSession } from "../../lib/session";

const SCOPE: Record<Doc["scope"], string> = { public: "公共", personal: "个人", temp: "临时" };
const STATUS: Record<string, string> = { ready: "Ready", parsing: "解析中", processing: "解析中", failed: "失败" };

/** 检查器「文档」面板：复用文档 API，只读展示公共与个人文档及真实状态。 */
export default function InspectorDocs() {
  const navigate = useNavigate();
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        await ensureSession();
        const [mine, shared] = await Promise.all([fetchPersonalDocs(), fetchPublicDocs()]);
        if (alive) setDocs([...mine, ...shared]);
      } catch (e) {
        if (alive) setError((e as Error).message);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  if (error) return <p className="font-label text-label-sm text-light-error dark:text-dark-error">{error}</p>;
  if (!docs) return <p className="font-label text-label-sm text-light-outline dark:text-dark-outline">加载中…</p>;

  return (
    <div className="flex flex-col">
      {docs.length === 0 && (
        <p className="font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">还没有文档。可在知识库页上传个人或公共文档。</p>
      )}
      {docs.map((d) => (
        <div key={d.id} className="flex items-center justify-between gap-gutter-sm border-b border-light-outline-variant py-1.5 last:border-0 dark:border-dark-outline-variant">
          <span className="min-w-0 truncate font-label text-label-md text-light-on-surface dark:text-dark-on-surface">{d.filename}</span>
          <span className="shrink-0 font-mono text-mono-sm text-light-outline dark:text-dark-outline">
            {SCOPE[d.scope]} · {STATUS[d.status] ?? d.status}
          </span>
        </div>
      ))}
      <button type="button" onClick={() => navigate("/documents")} className="mt-gutter-md self-start font-label text-label-sm text-light-primary underline underline-offset-2 dark:text-dark-primary">
        前往知识库
      </button>
    </div>
  );
}
