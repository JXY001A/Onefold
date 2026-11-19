/** 角色口径：与后端 deps.py 的白名单保持一致。 */

export type Role = "guest" | "member" | "admin" | "superadmin";

export const ROLE_LABEL: Record<Role, string> = {
  guest: "游客",
  member: "成员",
  admin: "管理员",
  superadmin: "超管",
};

/** 能否进入后台：与后端 require_role("admin", "superadmin") 一致。 */
export function canUseAdmin(role: Role | undefined): boolean {
  return role === "admin" || role === "superadmin";
}

/** 能否管理他人（改角色/停用）：只有超管，与后端 require_superadmin 一致。 */
export function canManageUsers(role: Role | undefined): boolean {
  return role === "superadmin";
}
