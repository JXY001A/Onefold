import type { Role } from "./roles";

export type NavItem = {
  to: string;
  label: string;
  icon: string;
  adminOnly?: boolean;
};

/** 模块导航：与路由对应，图标取设计稿 Material Symbols。 */
export const NAV_ITEMS: NavItem[] = [
  { to: "/chat", label: "研究对话", icon: "chat_bubble_outline" },
  { to: "/documents", label: "知识库", icon: "folder_open" },
  { to: "/memory", label: "研究记忆", icon: "psychology" },
  { to: "/skills", label: "Skill", icon: "extension" },
  { to: "/admin", label: "后台", icon: "admin_panel_settings", adminOnly: true },
];

export function visibleNav(role: Role | undefined, isAdmin: boolean): NavItem[] {
  return NAV_ITEMS.filter((n) => !n.adminOnly || isAdmin);
}