import { formatDate, type AccessRequest } from "../../lib/admin";

type Props = {
  requests: AccessRequest[];
  busy: boolean;
  onApprove: (id: string) => void;
};

/** 体验码申请：保留在后端，但产品上游客已可直接使用，不再需要申请。 */
export default function RequestTable({ requests, busy, onApprove }: Props) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs text-slate-500">
          <tr>
            <th className="px-4 py-2">昵称</th>
            <th className="px-4 py-2">用途</th>
            <th className="px-4 py-2">状态</th>
            <th className="px-4 py-2">体验码</th>
            <th className="px-4 py-2">申请时间</th>
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
              <td className="px-4 py-3 text-slate-500">{formatDate(r.created_at)}</td>
              <td className="px-4 py-3 text-right">
                {r.status === "pending" && (
                  <button
                    disabled={busy}
                    className="underline disabled:opacity-40"
                    onClick={() => onApprove(r.id)}
                  >
                    通过
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {requests.length === 0 && <p className="px-4 py-6 text-sm text-slate-500">暂无申请。</p>}
    </div>
  );
}
