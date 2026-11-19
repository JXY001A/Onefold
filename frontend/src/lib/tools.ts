/** 工具展示用的类型与文案：搜索结果、抓取页、工具名映射。 */

/** 一条搜索命中 */
export type ToolItem = {
  title: string;
  url: string;
  site?: string;
  date?: string;
  snippet?: string;
};

/** 工具的结构化结果（后端 tool_calls.data_json / SSE detail） */
export type ToolData = {
  kind: "search" | "fetch";
  query?: string;
  url?: string;
  title?: string;
  chars?: number;
  items?: ToolItem[];
  snippet?: string;
};

export const TOOL_LABEL: Record<string, string> = {
  web_search: "联网搜索",
  fetch_url: "读取网页",
};

export function toolLabel(name: string): string {
  return TOOL_LABEL[name] ?? name;
}

/** 这条工具一共带回多少条网页（抓取算 1 条） */
export function hitCount(data?: ToolData): number {
  if (!data) return 0;
  return data.kind === "fetch" ? 1 : (data.items?.length ?? 0);
}

/** 参数里最能说明「干了啥」的那一项；结构化结果优先（参数可能被截断） */
export function toolTarget(args?: string, data?: ToolData): string {
  if (data?.query) return data.query;
  if (data?.url) return data.url;
  if (!args) return "";
  try {
    const parsed = JSON.parse(args) as { query?: string; url?: string };
    return parsed.query ?? parsed.url ?? "";
  } catch {
    return "";
  }
}

/** 压成一行并截断，列表里不换行 */
export function clip(text: string, max: number): string {
  const flat = text.replace(/\s+/g, " ").trim();
  return flat.length > max ? `${flat.slice(0, max)}…` : flat;
}
