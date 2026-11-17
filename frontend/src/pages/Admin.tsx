import { useEffect, useState } from "react";

type AccessRequest = {
  id: string;
  name: string | null;
  contact: string | null;
  purpose: string | null;
  status: string;
  code: string | null;
  created_at: string | null;
};

type Usage = {
  user_id: string;
  day: string;
  messages: number;
  tokens_in: number;
  tokens_out: number;
  tool_calls: number;
};

export default function Admin() {
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [usage, setUsage] = useState<Usage[]>([]);

  const load = async () => {
    const [r1, r2] = await Promise.all([
      fetch("/api/admin/requests").then((r) => r.json()),
      fetch("/api/admin/usage").then((r) => r.json()),
    ]);
    setRequests(r1);
    setUsage(r2);
  };

  useEffect(() => {
    load();
  }, []);

  const approve = async (id: string) => {
    await fetch(`/api/admin/requests/${id}/approve`, { method: "POST" });
    load();
  };

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-3 text-lg font-semibold">体验码申请</h2>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="px-4 py-2">昵称</th>
                <th className="px-4 py-2">用途</th>
                <th className="px-4 py-2">状态</th>
                <th className="px-4 py-2">体验码</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">{r.name ?? "-"}</td>
                  <td className="px-4 py-3">{r.purpose ?? "-"}</td>
                  <td className="px-4 py-3">{r.status}</td>
                  <td className="px-4 py-3 font-mono text-xs">{r.code ?? "-"}</td>
                  <td className="px-4 py-3 text-right">
                    {r.status === "pending" && (
                      <button className="text-slate-900 underline" onClick={() => approve(r.id)}>
                        通过
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {requests.length === 0 && (
                <tr>
                  <td className="px-4 py-6 text-slate-500" colSpan={5}>
                    暂无申请。
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">每日用量</h2>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="px-4 py-2">用户</th>
                <th className="px-4 py-2">日期</th>
                <th className="px-4 py-2">消息</th>
                <th className="px-4 py-2">输入 token</th>
                <th className="px-4 py-2">输出 token</th>
                <th className="px-4 py-2">工具调用</th>
              </tr>
            </thead>
            <tbody>
              {usage.map((u) => (
                <tr key={`${u.user_id}-${u.day}`} className="border-t border-slate-100">
                  <td className="px-4 py-3">{u.user_id}</td>
                  <td className="px-4 py-3">{u.day}</td>
                  <td className="px-4 py-3">{u.messages}</td>
                  <td className="px-4 py-3">{u.tokens_in}</td>
                  <td className="px-4 py-3">{u.tokens_out}</td>
                  <td className="px-4 py-3">{u.tool_calls}</td>
                </tr>
              ))}
              {usage.length === 0 && (
                <tr>
                  <td className="px-4 py-6 text-slate-500" colSpan={6}>
                    暂无用量。
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
