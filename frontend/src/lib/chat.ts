/** 会话相关的类型与请求封装。 */

import { responseErrorText } from "./http";
import type { ToolData } from "./tools";

export type ToolRun = {
  id: string;
  name: string;
  status: "running" | "ok" | "error";
  summary?: string;
  args?: string; // 调用参数原文（可能是被截断的 JSON）
  data?: ToolData; // 结构化结果：搜索命中的链接与简介
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  tools?: ToolRun[]; // 本轮的工具痕迹（仅界面上用，不下发给模型）
};

/** 侧栏一条会话。后端字段是 snake_case，这里统一转成前端习惯的驼峰。 */
export type Conversation = {
  id: string;
  title: string;
  updatedAt: string;
};

type ConversationRow = {
  conversation_id: string;
  title: string;
  updated_at: string;
};

type MessageRow = {
  role: "user" | "assistant" | "tool";
  content: string;
  created_at: string;
  tool_call_id?: string | null;
  summary?: string | null;
  tool_ok?: boolean | null; // 审计表里的成败；老数据没有这一项
  tool_data?: ToolData | null; // 结构化结果（搜索结果列表等）
  tool_calls?: { id: string; name: string; arguments: string }[] | null;
};

/** 近 days 天内有过活动的会话，按活跃时间倒序（后端已排好）。 */
export async function fetchConversations(days = 20): Promise<Conversation[]> {
  const res = await fetch(`/api/conversations?days=${days}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error(`加载会话列表失败：${await responseErrorText(res)}`);
  const rows: ConversationRow[] = await res.json();
  return rows.map((r) => ({
    id: r.conversation_id,
    title: r.title,
    updatedAt: r.updated_at,
  }));
}

/**
 * 后端存的是「协议原样」：assistant(带 tool_calls) + tool 行交替出现。
 * 折叠规则：一轮一个气泡，assistant 文本拼接，tool 行并进 tools。
 */
function foldRows(rows: MessageRow[]): ChatMessage[] {
  const out: ChatMessage[] = [];
  for (const row of rows) {
    if (row.role === "user") {
      out.push({ role: "user", content: row.content });
      continue;
    }
    const tail = out[out.length - 1];
    const current: ChatMessage =
      tail && tail.role === "assistant" ? tail : { role: "assistant", content: "", tools: [] };
    if (current !== tail) out.push(current);

    if (row.role === "assistant") {
      if (row.content) {
        current.content = current.content ? `${current.content}\n\n${row.content}` : row.content;
      }
      for (const c of row.tool_calls ?? []) {
        current.tools = [
          ...(current.tools ?? []),
          { id: c.id, name: c.name, status: "running", args: c.arguments },
        ];
      }
    } else {
      // 成败优先看审计表（tool_ok），没有则退回结果文案判断
      const ok = row.tool_ok ?? !/失败|超时|不允许|未完成/.test(row.summary ?? "");
      current.tools = (current.tools ?? []).map((t) =>
        t.id === row.tool_call_id
          ? { ...t, status: ok ? "ok" : "error", summary: row.summary || undefined, data: row.tool_data ?? undefined }
          : t,
      );
    }
  }
  return out;
}

/** 某个会话的全部消息（按时间正序）。无权或不存在时后端返回 404。 */
export async function fetchMessages(conversationId: string): Promise<ChatMessage[]> {
  const res = await fetch(`/api/conversations/${conversationId}/messages`, {
    credentials: "include",
  });
  if (res.status === 404) throw new Error("会话不存在或无权访问");
  if (!res.ok) throw new Error(`加载历史消息失败：${await responseErrorText(res)}`);
  const rows: MessageRow[] = await res.json();
  return foldRows(rows);
}

/** 侧栏显示用的简短时间：今天显示时分，更早显示月-日。 */
export function formatTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const today = new Date();
  const sameDay =
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate();
  if (sameDay) {
    return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  }
  return `${date.getMonth() + 1}-${date.getDate()}`;
}