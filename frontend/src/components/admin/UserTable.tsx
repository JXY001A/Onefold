import { formatDate, type AdminUser } from "../../lib/admin";
import { ROLE_LABEL } from "../../lib/roles";

type Props = {
  users: AdminUser[];
  /** 只有超管能改角色/停用账号，与后端 require_superadmin 一致 */
  canManage: boolean;
  busy: boolean;
  onRole: (id: string, role: "member" | "admin") => void;
  onStatus: (id: string, status: "active" | "disabled") => void;
};

/** 用户列表：管理员只看，超管多一列操作。 */
export default function UserTable({ users, canManage, busy, onRole, onStatus }: Props) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs text-slate-500">
          <tr>
            <th className="px-4 py-2">用户名</th>
            <th className="px-4 py-2">邮箱</th>
            <th className="px-4 py-2">角色</th>
            <th className="px-4 py-2">状态</th>
            <th className="px-4 py-2">注册时间</th>
            {canManage && <th className="px-4 py-2 text-right">操作</th>}
          </tr>
        </thead>
        <tbody>
          {users.map((u) => {
            const isSuper = u.role === "superadmin";
            return (
              <tr key={u.id} className="border-t border-slate-100">
                <td className="px-4 py-3">{u.username}</td>
                <td className="px-4 py-3 text-slate-500">{u.email ?? "—"}</td>
                <td className="px-4 py-3">{ROLE_LABEL[u.role] ?? u.role}</td>
                <td className={`px-4 py-3 ${u.status === "active" ? "" : "text-red-600"}`}>
                  {u.status === "active" ? "正常" : "已停用"}
                </td>
                <td className="px-4 py-3 text-slate-500">{formatDate(u.created_at)}</td>
                {canManage && (
                  <td className="px-4 py-3 text-right">
                    {isSuper ? (
                      <span className="text-xs text-slate-400">超管只能在库里改</span>
                    ) : (
                      <div className="flex justify-end gap-3">
                        <button
                          disabled={busy}
                          className="underline disabled:opacity-40"
                          onClick={() => onRole(u.id, u.role === "admin" ? "member" : "admin")}
                        >
                          {u.role === "admin" ? "撤销管理员" : "设为管理员"}
                        </button>
                        <button
                          disabled={busy}
                          className="underline disabled:opacity-40"
                          onClick={() => onStatus(u.id, u.status === "active" ? "disabled" : "active")}
                        >
                          {u.status === "active" ? "停用" : "启用"}
                        </button>
                      </div>
                    )}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
      {users.length === 0 && <p className="px-4 py-6 text-sm text-slate-500">暂无用户。</p>}
    </div>
  );
}
