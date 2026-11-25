/** 身份与角色：与后端 /api/auth/* 一一对应。 */

import { apiErrorText, responseErrorText } from "./http";
import type { Role } from "./roles";

export type { Role };

export type Me = {
  id: string;
  kind: "user" | "guest";
  role: Role;
  /** 展示昵称（注册时默认取邮箱 @ 前部分） */
  username: string | null;
  email: string | null;
  /** 游客为「已用/上限」轮次；登录用户不限量，为 null */
  quota: { used: number; limit: number } | null;
};

export type CodePurpose = "register" | "reset";

type RegisterInput = { email: string; code: string; password: string; username?: string };
type ResetInput = { email: string; code: string; password: string };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(apiErrorText(data, res.status));
  return data as T;
}

export function login(account: string, password: string): Promise<Me> {
  return request<Me>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ account, password }),
  });
}

export function register(input: RegisterInput): Promise<Me> {
  return request<Me>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** 发送邮箱验证码；dev 模式（后端没配 SMTP）会带回 devCode 方便联调。 */
export async function sendCode(
  email: string,
  purpose: CodePurpose,
): Promise<{ expiresIn: number; devCode?: string }> {
  const data = await request<{ expires_in: number; dev_code?: string }>("/api/auth/email-code", {
    method: "POST",
    body: JSON.stringify({ email, purpose }),
  });
  return { expiresIn: data.expires_in, devCode: data.dev_code };
}

export async function resetPassword(input: ResetInput): Promise<void> {
  await request("/api/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** 当前身份；既未登录、访客也已过期时后端返回 401。 */
export async function fetchMe(): Promise<Me> {
  const res = await fetch("/api/auth/me", { credentials: "include" });
  if (!res.ok) throw new Error(await responseErrorText(res));
  return (await res.json()) as Me;
}

/** 退出登录后立即降级为访客（后端会同时清掉两个 Cookie）。 */
export async function logout(): Promise<Me> {
  await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
  await fetch("/api/auth/guest", { method: "POST", credentials: "include" });
  return fetchMe();
}