import { useEffect, useState, type ChangeEvent } from "react";

type Doc = {
  id: string;
  filename: string;
  size: number;
  kind: string;
  status: string;
  expires_at: string | null;
};

export default function Documents() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const res = await fetch("/api/documents");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setDocs(await res.json());
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const upload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    await fetch("/api/documents", { method: "POST", body: fd });
    e.target.value = "";
    load();
  };

  const remove = async (id: string) => {
    await fetch(`/api/documents/${id}`, { method: "DELETE" });
    load();
  };

  const collect = async (id: string) => {
    await fetch(`/api/documents/${id}/collect`, { method: "POST" });
    load();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">文档</h2>
        <label className="cursor-pointer rounded-lg border border-slate-300 px-4 py-2 text-sm">
          上传
          <input type="file" className="hidden" onChange={upload} />
        </label>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        {docs.length === 0 ? (
          <p className="p-6 text-sm text-slate-500">还没有文档，先上传一个 PDF / MD / TXT。</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="px-4 py-2">文件名</th>
                <th className="px-4 py-2">类型</th>
                <th className="px-4 py-2">状态</th>
                <th className="px-4 py-2">大小</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">{d.filename}</td>
                  <td className="px-4 py-3">{d.kind}</td>
                  <td className="px-4 py-3">{d.status}</td>
                  <td className="px-4 py-3">{Math.round(d.size / 1024)} KB</td>
                  <td className="space-x-2 px-4 py-3 text-right">
                    {d.kind === "temp" && (
                      <button className="text-slate-600 underline" onClick={() => collect(d.id)}>
                        收藏
                      </button>
                    )}
                    <button className="text-red-600 underline" onClick={() => remove(d.id)}>
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
