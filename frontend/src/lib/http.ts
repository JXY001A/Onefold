/** 把后端返回体翻译成给人看的提示文案。 */

const STATUS_TEXT: Record<number, string> = {
  400: "请求参数不正确，请检查后重试",
  401: "登录状态已失效，请重新登录",
  403: "没有权限执行这个操作",
  404: "目标不存在或已被删除",
  409: "操作冲突，请刷新后重试",
  413: "文件超过大小限制",
  429: "操作太频繁，请稍后再试",
  500: "服务器出错了，请稍后重试",
  502: "上游服务暂时不可用，请稍后重试",
  503: "服务暂时不可用，请稍后重试",
};

/**
 * FastAPI 的错误体有两种形状：
 *   {"detail": "文档数量已达上限"}
 *   {"detail": [{"msg": "Value error, 密码至少 8 位"}]}（pydantic 校验）
 * 认不出时按状态码给中文兜底，避免把 HTTP 码和 JSON 原文丢给用户。
 */
export function apiErrorText(data: unknown, status: number): string {
  const detail = (data as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string };
    if (first?.msg) return first.msg.replace("Value error, ", "");
  }
  return STATUS_TEXT[status] ?? `请求失败（${status}）`;
}

/** 读取响应体并生成提示文案；响应体不是 JSON 时同样走状态码兜底。 */
export async function responseErrorText(res: Response): Promise<string> {
  const data = await res.json().catch(() => null);
  return apiErrorText(data, res.status);
}

/** 统一请求：自动带 Cookie，失败时抛出可直接展示给用户的文案。 */
export async function apiRequest<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  if (!res.ok) throw new Error(await responseErrorText(res));
  return (await res.json()) as T;
}