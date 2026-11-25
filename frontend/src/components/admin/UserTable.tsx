import { formatDate, type AdminUser } from "../../lib/admin";
import { ROLE_LABEL } from "../../lib/roles";
import { ActionLink, Badge, EmptyText } from "../ui/kit";
import { TableShell, Td, Th, THead } from "../ui/table";

type Props = {
  users: AdminUser[];
  canManage: boolean;
  busy: boolean;
  onRole: (id: string, role: "member" | "admin") => void;
  onStatus: (id: string, status: "active" | "disabled") => void;
};

/** 用户操作：管理员只读；超管行只能库改；其余可切换角色与启停。 */
function UserActions({ user, canManage, busy, onRole, onStatus }: { user: AdminUser } & Omit<Props, "users">) {
  if (!canManage) return null;
  if (user.role === "superadmin") {
    return <span className="font-label text-label-sm text-light-outline dark:text-dark-outline">超管只能在库里改</span>;
  }
  return (
    <div className="flex items-center justify-end gap-gutter-md">
      <button
        type="button"
        disabled={busy}
        onClick={() => onRole(user.id, user.role === "admin" ? "member" : "admin")}
        className="font-label text-label-sm text-light-on-primary-container underline underline-offset-2 disabled:opacity-40 dark:text-dark-primary"
      >
        {user.role === "admin" ? "撤销管理员" : "设为管理员"}
      </button>
      <ActionLink
        disabled={busy}
        tone={user.status === "active" ? "danger" : "primary"}
        onClick={() => onStatus(user.id, user.status === "active" ? "disabled" : "active")}
      >
        {user.status === "active" ? "停用" : "启用"}
      </ActionLink>
    </div>
  );
}

/** 用户列表：桌面表格 + <lg 卡片；角色徽章与操作颜色按设计稿。 */
export default function UserTable({ users, canManage, busy, onRole, onStatus }: Props) {
  const empty = <EmptyText className="py-gutter-md">暂无用户。</EmptyText>;

  return (
    <>
      <div className="hidden lg:block">
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
            {users.map((u) => (
              <tr key={u.id}>
                <Td>{u.username}</Td>
                <Td className="text-light-on-surface-variant dark:text-dark-on-surface-variant">{u.email ?? "—"}</Td>
                <Td><Badge>{ROLE_LABEL[u.role] ?? u.role}</Badge></Td>
                <Td className={u.status === "active" ? "" : "text-light-error dark:text-dark-error"}>{u.status === "active" ? "正常" : "已停用"}</Td>
                <Td className="text-light-on-surface-variant dark:text-dark-on-surface-variant">{formatDate(u.created_at)}</Td>
                {canManage && (
                  <Td className="text-right">
                    <UserActions user={u} canManage={canManage} busy={busy} onRole={onRole} onStatus={onStatus} />
                  </Td>
                )}
              </tr>
            ))}
            {users.length === 0 && <tr><Td colSpan={canManage ? 6 : 5}>{empty}</Td></tr>}
          </tbody>
        </TableShell>
      </div>

      <div className="flex flex-col gap-gutter-sm lg:hidden">
        {users.length === 0 && <div className="rounded border border-light-outline-variant p-gutter-md dark:border-dark-outline-variant">{empty}</div>}
        {users.map((u) => (
          <div key={u.id} className="flex flex-col gap-2 rounded border border-light-outline-variant bg-light-surface p-gutter-md dark:border-dark-outline-variant dark:bg-dark-surface">
            <div className="flex items-center justify-between gap-gutter-sm">
              <span className="min-w-0 truncate font-label text-label-md text-light-on-surface dark:text-dark-on-surface">{u.username}</span>
              <Badge>{ROLE_LABEL[u.role] ?? u.role}</Badge>
            </div>
            <div className="flex flex-wrap items-center gap-gutter-sm font-label text-label-sm text-light-outline dark:text-dark-outline">
              <span>{u.email ?? "—"}</span>
              <span>·</span>
              <span className={u.status === "active" ? "" : "text-light-error dark:text-dark-error"}>{u.status === "active" ? "正常" : "已停用"}</span>
              <span>·</span>
              <span>{formatDate(u.created_at)}</span>
            </div>
            {canManage && (
              <div className="flex justify-end">
                <UserActions user={u} canManage={canManage} busy={busy} onRole={onRole} onStatus={onStatus} />
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
