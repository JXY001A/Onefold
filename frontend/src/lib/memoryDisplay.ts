import type { MemoryItem } from "./memory";

/** 记忆展示：类型与日期均为真实字段。 */
export function kindLabel(kind: MemoryItem["kind"]): string {
  return kind === "card" ? "卡片记忆" : "笔记记忆";
}

export function memoryDate(iso: string | null): string {
  return iso ? iso.slice(0, 10) : "未记录日期";
}
