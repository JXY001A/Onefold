"""工具注册表：声明给模型的 tools，并负责执行与审计。

只放「进程内、无隔离需求、需要用户上下文」的工具：联网搜索与网页抓取。
将来接 RAG、代码执行时往 SPECS 里加一条、在 execute 里加一个分支即可，runtime 不用改。
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass

from ..config import settings
from ..services import tools as web
from ..services.tool_audit import save_tool_call

log = logging.getLogger("onefold.tools")

_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "联网搜索实时信息。适合新闻、天气、价格、赛事、新版本发布及近期事件，以及你不确定或可能过时的事实。"
            "返回标题、来源、时间与摘要。中文查询效果最好；支持 site:github.com、lang:zh 等语法。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索词，1~128 字"},
                    "count": {
                        "type": "integer", 
                        "description": "返回条数，1~50，默认 5",
                        "minimum": 1, "maximum": 50
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "抓取指定网页的正文（Markdown）。用户给出链接，或搜索摘要不足以回答、需要全文时使用。只支持公网 http/https。",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "要抓取的网页地址"}},
                "required": ["url"],
            },
        },
    },
]


@dataclass
class ToolContext:
    """一次工具执行需要的上下文（身份绝不从模型给的参数里取）。"""

    run_id: str
    query: str  # 本轮用户原始问题，用作搜索的 ori_question
    step: int


@dataclass
class ToolResult:
    text: str  # 回填给模型的 tool 消息
    summary: str  # 前端与审计用的短摘要
    ok: bool
    elapsed_ms: int = 0
    error: str | None = None
    data: dict | None = None  # 结构化结果（搜索结果列表等），只给前端看


def available() -> list[dict]:
    """当前可用工具的 schema；关闭开关时返回空列表（行为与未接入一致）。"""
    return _SPECS if settings.search_enabled else []


async def execute(name: str, raw_args: str, ctx: ToolContext, call_id: str) -> ToolResult:
    """执行一次工具调用。**永不抛异常**：失败也要转成给模型看的文本。"""
    started = time.monotonic()
    text, summary, ok, error, data = "", "", True, None, None

    try:
        args = json.loads(raw_args or "{}")
        if not isinstance(args, dict):
            raise ValueError("参数必须是 JSON 对象")
        # 超出指定时间会取消请求
        async with asyncio.timeout(settings.agent_tool_timeout_s):
            if name == "web_search":
                text, n, data = await web.search(
                    str(args.get("query") or ""), args.get("count"), ctx.query
                )
                summary = f"找到 {n} 条结果" if n else "没有找到结果"
            elif name == "fetch_url":
                text, size, data = await web.fetch(str(args.get("url") or ""))
                summary = f"读取 {size} 字" if size else "没有可读正文"
            else:
                raise ValueError(f"未知工具 {name}")
    except TimeoutError:
        ok, error = False, "执行超时"
        text = f"{name} 执行超时，请基于已有信息作答，或告知用户稍后再试。"
        summary = error
    except Exception as exc:  # noqa: BLE001 - 工具失败不能让整轮对话崩掉
        ok = False
        error = str(exc) or type(exc).__name__
        text = f"{name} 执行失败：{error}。可以换个方式再试，或直接告知用户。"
        summary = error

    elapsed = int((time.monotonic() - started) * 1000)
    try:
        save_tool_call(
            run_id=ctx.run_id, tool_name=name, args=raw_args or "", summary=summary, data=data,
            status="ok" if ok else "error", elapsed_ms=elapsed, llm_call_id=call_id,
            step=ctx.step, error=error,
        )
    except Exception:  # 审计写失败不影响对话
        log.warning("写 tool_calls 失败", exc_info=True)

    return ToolResult(text=text, summary=summary, ok=ok, elapsed_ms=elapsed, error=error, data=data)
