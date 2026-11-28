import type { MemoryItem } from "./memory";

/** 记忆展示：类型与日期均为真实字段。 */
export function kindLabel(kind: MemoryItem["kind"]): string {
  return kind === "card" ? "卡片记忆" : "笔记记忆";
}

export function memoryDate(iso: string | null): string {
  return iso ? iso.slice(0, 10) : "未记录日期";
}

/** 设计稿时间格式：YYYY-MM-DD HH:mm（记忆中心列表/详情用）。 */
export function memoryDateTime(iso: string | null): string {
  if (!iso) return "未记录时间";
  return `${iso.slice(0, 10)} ${iso.slice(11, 16)}`;
}
