/** 记忆接口：卡片/笔记的读取与增删改，路径与后端 /api/memory 一致。 */

import { apiRequest } from "./http";

export type MemoryItem = {
  id: string;
  kind: "card" | "note";
  category: string | null;
  key: string | null;
  value: unknown;
  text: string;
  confidence: number;
  mention_count: number;
  pinned: boolean;
  happened_at: string | null;
  updated_at: string | null;
};

export type MemoryData = {
  enabled: boolean;
  cards: MemoryItem[];
  notes: MemoryItem[];
};

const JSON_HEADERS = { "Content-Type": "application/json" };

export function fetchMemory(): Promise<MemoryData> {
  return apiRequest<MemoryData>("/api/memory");
}

export function setMemoryEnabled(enabled: boolean): Promise<unknown> {
  return apiRequest("/api/memory/settings", {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify({ enabled }),
  });
}

export function updateMemoryText(id: string, text: string): Promise<unknown> {
  return apiRequest(`/api/memory/${id}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify({ text }),
  });
}

export function deleteMemory(id: string): Promise<unknown> {
  return apiRequest(`/api/memory/${id}`, { method: "DELETE" });
}

export function clearMemory(): Promise<unknown> {
  return apiRequest("/api/memory", { method: "DELETE" });
}