import type { Doc } from "./documents";

/** 文档展示：真实状态/作用域的人类可读文案（不臆造状态）。 */
export function scopeLabel(scope: Doc["scope"]): string {
  if (scope === "public") return "公共知识库 · 只读";
  if (scope === "personal") return "个人知识库";
  return "临时文档";
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = { uploaded: "已上传", pending: "排队中", parsing: "解析中", ready: "Ready", failed: "失败" };
  return map[status] ?? status;
}

export function statusTone(status: string): string {
  if (status === "failed") return "text-light-error dark:text-dark-error";
  if (status === "ready") return "text-light-primary dark:text-dark-primary";
  return "text-light-warning dark:text-dark-warning";
}

export function formatSize(size: number): string {
  if (size < 1024) return `${size} B`;
  return `${Math.round(size / 1024)} KB`;
}
