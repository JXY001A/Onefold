"""Agent Runtime（骨架）：后续在这里实现 ReAct 循环。

事件类型与 docs/architecture.md 的 SSE 契约一致：
  token / tool_call / tool_result / citation / done / error
"""

from uuid import uuid4

from ..rag.retrieve import retrieve


class AgentRuntime:
    async def run(self, query: str, user_id: str | None = None, session_id: str | None = None):
        # TODO: 1) build_messages  2) 调 DeepSeek（带 tools）
        # TODO: 3) tool_calls → 执行 RAG/MCP → 回填  4) 循环到无 tool_calls
        chunks = retrieve(query, user_id=user_id, session_id=session_id)
        if chunks:
            yield {"type": "citation", "data": {"count": len(chunks)}}

        # 骨架回答：不调用外部模型，保证离线可跑
        text = (
            "归一骨架已启动。当前是占位回答；请实现 agent/runtime.py 的 ReAct 循环，"
            "并在 .env 配置 DEEPSEEK_API_KEY。"
        )
        for ch in text:
            yield {"type": "token", "data": {"delta": ch}}

        yield {"type": "done", "data": {"run_id": str(uuid4()), "usage": {}}}
