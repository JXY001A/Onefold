import type { UsageRow } from "../../lib/admin";

/** 每日用量：按用户 + 日期一行，管理员用来核对 token 消耗。 */
export default function UsageTable({ rows }: { rows: UsageRow[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
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
          {rows.map((u) => (
            <tr key={`${u.user_id}-${u.day}`} className="border-t border-slate-100">
              <td className="px-4 py-3 font-mono text-xs">{u.user_id}</td>
              <td className="px-4 py-3">{u.day}</td>
              <td className="px-4 py-3">{u.messages}</td>
              <td className="px-4 py-3">{u.tokens_in}</td>
              <td className="px-4 py-3">{u.tokens_out}</td>
              <td className="px-4 py-3">{u.tool_calls}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && <p className="px-4 py-6 text-sm text-slate-500">暂无用量。</p>}
    </div>
  );
}
