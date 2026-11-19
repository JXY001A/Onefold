"""DeepSeek 官方工具接口的 HTTP 客户端。

端点（与聊天共用同一把 api_key）：
    POST {base_url}/v1/tools/search   {query, count, ori_question, need_content}
    POST {base_url}/v1/tools/fetch    {url}

重试口径按官方文档：只重试 408 / 429 / 5xx；其它 4xx 说明参数或权限有问题，
重试只会重复扣费或重复失败，直接抛给上层转成「工具失败」文案。
"""

import asyncio

import httpx

from ...config import settings


class ToolError(Exception):
    """工具失败。str(exc) 是**给模型看的中文说明**，不含堆栈。"""


# 这些状态码代表「等一会儿可能就好了」
_RETRYABLE = {408, 429, 500, 502, 503, 504}

# 上游错误体里的 message 不一定适合直接给模型看，优先用这里的固定文案
_FRIENDLY = {
    401: "搜索服务鉴权失败（API Key 无效）",
    402: "搜索服务余额不足，请联系管理员",
    403: "该网页被安全策略拒绝访问",
    404: "该网页无法获取正文",
    429: "搜索请求过于频繁，请稍后再试",
    408: "搜索服务响应超时，请稍后再试",
}


async def post_tool(path: str, payload: dict) -> dict:
    """调用 /v1/tools/* 并返回 JSON；失败抛 ToolError。"""
    if not settings.api_key:
        raise ToolError("搜索服务未配置 API Key")
    # 构建 URL 和请求头
    url = settings.base_url.rstrip("/") + path
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    attempts = max(0, settings.tool_http_retries) + 1
    last: ToolError | None = None

    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=settings.tool_http_timeout_s) as client:
                resp = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException:
            last = ToolError("搜索服务响应超时，请稍后再试")
        except httpx.HTTPError as exc:
            last = ToolError(f"搜索服务连接失败：{type(exc).__name__}")
        else:
            if resp.status_code == 200:
                return resp.json()
            msg = _FRIENDLY.get(resp.status_code) or _upstream_message(resp)
            if resp.status_code not in _RETRYABLE:
                raise ToolError(msg)
            last = ToolError(msg)

        # 指数退避：0.5s、1s …… 最多两次重试，不让一次搜索拖住整轮对话
        if attempt + 1 < attempts:
            await asyncio.sleep(0.5 * (2**attempt))

    raise last or ToolError("搜索服务暂时不可用")


def _upstream_message(resp: httpx.Response) -> str:
    """兼容 OpenAI 错误格式 {error:{message}}，取不到就退回状态码。"""
    try:
        err = resp.json().get("error") or {}
        text = err.get("message") or ""
    except ValueError:
        text = ""
    return f"搜索服务返回 {resp.status_code}：{text[:120]}" if text else f"搜索服务返回 {resp.status_code}"
