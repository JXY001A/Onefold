"""Agent Runtime（骨架）：后续在这里实现 ReAct 循环。

事件类型与 docs/architecture.md 的 SSE 契约一致：
  token / tool_call / tool_result / citation / done / error
"""

from dataclasses import dataclass
from uuid import uuid4

from ..services.history import load_history
from ..services.llm import stream_chat
from ..rag.retrieve import retrieve
from .context import build_messages

class AgentRuntime:
    """Agent 运行时环境：调用 DeepSeek API、执行 RAG/MCP、处理工具调用等。"""

    def __init__(self) -> None:
        # 历史消息放实例属性：每个 AgentRuntime 实例独立。
        # 不要写成类级可变默认值（如 history = []），否则所有实例会共享同一个列表。
        self.history_conversations: list[dict] = []

    # 加载历史消息（按会话归属 owner_key 校验，登录用户与访客同一套规则）
    def load_history_conversation(
        self, owner_key: str | None = None, conversation_id: str | None = None
    ):
        self.history_conversations = load_history(owner_key or "", conversation_id)

    # 运行一次对话
    async def run(
        self,
        query: str,
        owner_key: str | None = None,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ):
        # TODO: 1) build_messages  2) 调 DeepSeek（带 tools）
        # TODO: 3) tool_calls → 执行 RAG/MCP → 回填  4) 循环到无 tool_calls
        self.load_history_conversation(owner_key, conversation_id)
        messages = build_messages(query, self.history_conversations)
        # 本轮构造的完整消息列表（含历史 + 当前问题）成为新的历史基准。
        # list(message) ： 一次浅拷贝
        self.history_conversations = list(messages)
        chunks = retrieve(query, user_id=user_id, conversation_id=conversation_id)
        
        # if chunks:
        #     yield {"type": "citation", "data": {"count": len(chunks)}}
        content = ""
        # stream_chat 的签名是 stream_chat(messages)，要传完整的消息列表
        async for chunk in stream_chat(messages):
            content += chunk
            yield {"type": "token", "data": {"delta": chunk}}
        
        yield {"type": "done", "data": {"run_id": str(uuid4()), "usage": {}}}
