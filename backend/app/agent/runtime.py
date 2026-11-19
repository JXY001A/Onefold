"""Agent Runtime：ReAct 循环（思考 → 调工具 → 再思考 → 作答）。

事件契约见 docs/architecture.md：token / tool_call / tool_result / done / error

设计要点：
    - runtime 不碰数据库：只维护 messages（发给 LLM 的完整上下文）与 transcript
      （要落库的 user/assistant/tool 三类消息），由 api 层统一写入。
    - 最后一步不再下发 tools，强制模型基于已有信息收尾，避免无限循环。
    - 工具失败也照常回填 tool 消息，让模型自己解释，而不是把异常抛给前端。
"""

from uuid import uuid4

from ..config import settings
from ..services.history import load_history
from ..services.llm import stream_with_tools
from ..rag.retrieve import retrieve
from . import tools as tool_registry
from .context import build_messages

BRIEF_MAX = 120


def _brief(raw: str) -> str:
    """工具参数摘要：前端只用来显示「搜了什么」，不必给全文。"""
    text = (raw or "").replace("\n", " ")
    return text[:BRIEF_MAX] + ("…" if len(text) > BRIEF_MAX else "")


def _openai_call(c: dict, step: int, i: int) -> dict:
    """把累加器里的调用转成 OpenAI 格式；上游没给 id 时自己造一个。"""
    return {
        "id": c.get("id") or f"call_{step}_{i}",
        "type": "function",
        "function": {"name": c.get("name") or "", "arguments": c.get("arguments") or "{}"},
    }


class AgentRuntime:
    """一次对话的执行器。实例只服务一轮请求，用完即弃。"""

    def __init__(self) -> None:
        # 发给 LLM 的完整消息（含 system），本轮内逐步追加 assistant / tool
        self.messages: list[dict] = []
        # 要落库的消息（不含 system），失败或被取消时也能拿到已完成的部分
        self.transcript: list[dict] = []

    async def run(
        self,
        query: str,
        run_id: str = "",
        owner_key: str | None = None,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ):
        history = load_history(owner_key or "", conversation_id)
        # retrieve 目前是空骨架，返回 []；转成 dict 以免往下游传 dataclass
        chunks = [
            {"filename": c.filename, "page": c.page, "text": c.text}
            for c in retrieve(query, user_id=user_id, conversation_id=conversation_id)
        ]
        messages = build_messages(query, history, rag_chunks=chunks)
        # 可用工具
        tools = tool_registry.available()
        self.messages = messages
        self.transcript = [{"role": "user", "content": query}]

        # 有工具才有循环；最后一步不给工具，用来强制收尾
        steps = settings.agent_max_steps if tools else 1
        for step in range(1, steps + 1):
            use_tools = tools if (tools and step < steps) else None
            content = ""
            calls: list[dict] = []

            async for ev in stream_with_tools(messages, use_tools):
                if ev["type"] == "delta":
                    content += ev["content"]
                    yield {"type": "token", "data": {"delta": ev["content"]}}
                elif ev["type"] == "tool_calls":
                    calls = ev["calls"]

            if not calls:
                final = {"role": "assistant", "content": content}
                messages.append(final)
                self.transcript.append(final)
                break

            assistant = {
                "role": "assistant",
                "content": content,
                "tool_calls": [_openai_call(c, step, i) for i, c in enumerate(calls)],
            }
            messages.append(assistant)
            self.transcript.append(assistant)

            ctx = tool_registry.ToolContext(run_id=run_id, query=query, step=step)
            for call in assistant["tool_calls"]:
                fn = call["function"]
                yield {
                    "type": "tool_call",
                    "data": {"id": call["id"], "name": fn["name"], "arguments": _brief(fn["arguments"])},
                }
                result = await tool_registry.execute(fn["name"], fn["arguments"], ctx, call["id"])
                yield {
                    "type": "tool_result",
                    "data": {"id": call["id"], "name": fn["name"], "ok": result.ok,
                             "summary": result.summary, "ms": result.elapsed_ms,
                             "detail": result.data},
                }
                # 每个调用都必须回填一条 tool 消息，否则下一轮上游报「悬空 tool_calls」
                tool_msg = {"role": "tool", "tool_call_id": call["id"], "name": fn["name"], "content": result.text}
                messages.append(tool_msg)
                self.transcript.append(tool_msg)

        yield {"type": "done", "data": {"run_id": run_id or str(uuid4()), "usage": {}}}
