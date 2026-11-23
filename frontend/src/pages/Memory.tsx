import { useEffect, useState } from "react";
import { ensureSession } from "../lib/session";

type MemoryItem = {
  id: string;
  kind: "card" | "note";
  category: string | null;
  key: string | null;
  value: unknown;
  text: string;
  confidence: number;
  mention_count: number;
  pinned: boolean;
  happened_at: string | null;
  updated_at: string | null;
};

type MemoryData = {
  enabled: boolean;
  cards: MemoryItem[];
  notes: MemoryItem[];
};

export default function Memory() {
  const [data, setData] = useState<MemoryData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      // 访客也要先拿到 guest_id，再访问记忆接口
      await ensureSession();
      const res = await fetch("/api/memory", { credentials: "include" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const toggle = async () => {
    if (!data) return;
    const res = await fetch("/api/memory/settings", {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !data.enabled }),
    });
    if (res.ok) setData({ ...data, enabled: !data.enabled });
  };

  const edit = async (item: MemoryItem) => {
    const next = window.prompt("编辑记忆内容（留空取消）", item.text);
    if (next === null || !next.trim()) return;
    const res = await fetch(`/api/memory/${item.id}`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: next.trim() }),
    });
    if (res.ok) load();
  };

  const remove = async (id: string) => {
    if (!window.confirm("删除这条记忆？")) return;
    const res = await fetch(`/api/memory/${id}`, {
      method: "DELETE",
      credentials: "include",
    });
    if (res.ok) load();
  };

  const clearAll = async () => {
    if (!window.confirm("清空全部记忆？该操作不可撤销。")) return;
    const res = await fetch("/api/memory", { method: "DELETE", credentials: "include" });
    if (res.ok) load();
  };

  if (loading) return <p className="text-sm text-slate-500">加载记忆…</p>;
  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!data) return null;

  const renderItem = (item: MemoryItem) => (
    <div key={item.id} className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-1 flex items-center gap-2 text-xs text-slate-500">
        <span className="rounded bg-slate-100 px-2 py-0.5">
          {/* 分类统一用中文，兼容后端归一化后的值；空值兜底也用中文 */}
          {item.category ?? "其他"}
        </span>
        {item.mention_count > 1 && <span>提到 {item.mention_count} 次</span>}
        {item.pinned && <span>已固定</span>}
      </div>
      <p className="whitespace-pre-wrap text-sm leading-6">{item.text}</p>
      <div className="mt-2 flex gap-3 text-xs">
        <button className="text-slate-600 underline" onClick={() => edit(item)}>
          编辑
        </button>
        <button className="text-red-600 underline" onClick={() => remove(item.id)}>
          删除
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">我的记忆</h2>
          <p className="mt-1 text-sm text-slate-500">
            跨会话保存的偏好、身份与背景；你可以随时修改或删除。
          </p>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <button className="text-slate-600 underline" onClick={toggle}>
            {data.enabled ? "关闭记忆" : "开启记忆"}
          </button>
          <button className="text-red-600 underline" onClick={clearAll}>
            清空
          </button>
        </div>
      </div>

      {!data.enabled && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          记忆已关闭：不会提取新记忆，也不会注入已有记忆。
        </p>
      )}

      <section>
        <h3 className="mb-2 text-sm font-medium text-slate-700">卡片</h3>
        {data.cards.length === 0 ? (
          <p className="text-sm text-slate-500">暂无卡片记忆。</p>
        ) : (
          <div className="space-y-2">{data.cards.map(renderItem)}</div>
        )}
      </section>

      <section>
        <h3 className="mb-2 text-sm font-medium text-slate-700">笔记</h3>
        {data.notes.length === 0 ? (
          <p className="text-sm text-slate-500">暂无笔记记忆。</p>
        ) : (
          <div className="space-y-2">{data.notes.map(renderItem)}</div>
        )}
      </section>
    </div>
  );
}
