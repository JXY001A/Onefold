/** 会话相关的类型与请求封装。 */

export type ToolRun = {
  id: string;
  name: string;
  status: "running" | "ok" | "error";
  summary?: string;
};

/** 页面内一条消息（历史消息只有 role/content，tools 仅本次会话内有效）。 */
export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  tools?: ToolRun[];
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
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

/** 近 days 天内有过活动的会话，按活跃时间倒序（后端已排好）。 */
export async function fetchConversations(days = 20): Promise<Conversation[]> {
  const res = await fetch(`/api/conversations?days=${days}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error(`加载会话列表失败: HTTP ${res.status}`);
  const rows: ConversationRow[] = await res.json();
  return rows.map((r) => ({
    id: r.conversation_id,
    title: r.title,
    updatedAt: r.updated_at,
  }));
}

/** 某个会话的全部消息（按时间正序）。无权或不存在时后端返回 404。 */
export async function fetchMessages(conversationId: string): Promise<ChatMessage[]> {
  const res = await fetch(`/api/conversations/${conversationId}/messages`, {
    credentials: "include",
  });
  if (res.status === 404) throw new Error("会话不存在或无权访问");
  if (!res.ok) throw new Error(`加载历史消息失败: HTTP ${res.status}`);
  const rows: MessageRow[] = await res.json();
  return rows.map((r) => ({ role: r.role, content: r.content }));
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