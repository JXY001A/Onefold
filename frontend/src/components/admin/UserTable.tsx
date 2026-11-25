import { formatDate, type AdminUser } from "../../lib/admin";
import { ROLE_LABEL } from "../../lib/roles";
import { ActionLink, EmptyText } from "../ui/kit";
import { TableShell, Td, Th, THead } from "../ui/table";

type Props = {
  users: AdminUser[];
  canManage: boolean;
  busy: boolean;
  onRole: (id: string, role: "member" | "admin") => void;
  onStatus: (id: string, status: "active" | "disabled") => void;
};

/** 用户列表：管理员只看，超管多一列操作。 */
export default function UserTable({ users, canManage, busy, onRole, onStatus }: Props) {
  return (
    <TableShell>
      <THead>
        <tr>
          <Th>用户名</Th>
          <Th>邮箱</Th>
          <Th>角色</Th>
          <Th>状态</Th>
          <Th>注册时间</Th>
          {canManage && <Th className="text-right">操作</Th>}
        </tr>
      </THead>
      <tbody>
        {users.map((u) => {
          const isSuper = u.role === "superadmin";
          return (
            <tr key={u.id}>
              <Td>{u.username}</Td>
              <Td className="text-light-on-surface-variant dark:text-dark-on-surface-variant">{u.email ?? "—"}</Td>
              <Td>{ROLE_LABEL[u.role] ?? u.role}</Td>
              <Td className={u.status === "active" ? "" : "text-light-error dark:text-dark-error"}>{u.status === "active" ? "正常" : "已停用"}</Td>
              <Td className="text-light-on-surface-variant dark:text-dark-on-surface-variant">{formatDate(u.created_at)}</Td>
              {canManage && (
                <Td className="text-right">
                  {isSuper ? (
                    <span className="font-label text-label-sm text-light-outline dark:text-dark-outline">超管只能在库里改</span>
                  ) : (
                    <div className="flex justify-end gap-gutter-md">
                      <ActionLink disabled={busy} onClick={() => onRole(u.id, u.role === "admin" ? "member" : "admin")}>{u.role === "admin" ? "撤销管理员" : "设为管理员"}</ActionLink>
                      <ActionLink disabled={busy} tone={u.status === "active" ? "danger" : "primary"} onClick={() => onStatus(u.id, u.status === "active" ? "disabled" : "active")}>{u.status === "active" ? "停用" : "启用"}</ActionLink>
                    </div>
                  )}
                </Td>
              )}
            </tr>
          );
        })}
        {users.length === 0 && <tr><Td colSpan={canManage ? 6 : 5}><EmptyText className="py-gutter-md">暂无用户。</EmptyText></Td></tr>}
      </tbody>
    </TableShell>
  );
}