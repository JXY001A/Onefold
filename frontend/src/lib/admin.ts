/** 后台接口封装：统一带 Cookie、统一解析后端 detail 错误。 */

import { apiErrorText } from "./http";
import type { Role } from "./roles";

export type AdminUser = {
  id: string;
  username: string;
  email: string | null;
  role: Role;
  status: "active" | "disabled";
  created_at: string | null;
};

export type UsageRow = {
  user_id: string;
  day: string;
  messages: number;
  tokens_in: number;
  tokens_out: number;
  tool_calls: number;
};

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(apiErrorText(data, res.status));
  return data as T;
}

export function fetchUsers(): Promise<AdminUser[]> {
  return call<AdminUser[]>("/api/admin/users");
}

export function changeRole(id: string, role: "member" | "admin"): Promise<unknown> {
  return call(`/api/admin/users/${id}/role`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export function changeStatus(id: string, status: "active" | "disabled"): Promise<unknown> {
  return call(`/api/admin/users/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function fetchUsage(): Promise<UsageRow[]> {
  return call<UsageRow[]>("/api/admin/usage");
}

/** ISO 时间取日期部分，够后台列表用。 */
export function formatDate(iso: string | null): string {
  return iso ? iso.slice(0, 10) : "-";
}
