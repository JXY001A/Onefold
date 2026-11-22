"""DeepSeek（OpenAI 兼容）客户端。"""

from openai import AsyncOpenAI

from ..config import settings


def get_client() -> AsyncOpenAI:
    if not settings.api_key:
        raise RuntimeError("API_KEY is not set")
    return AsyncOpenAI(
        api_key=settings.api_key,
        base_url=settings.base_url,
    )


async def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
):
    """非流式调用；max_tokens/temperature 供历史摘要等内部任务使用。"""
    client = get_client()
    extra: dict = {}
    if max_tokens is not None:
        extra["max_tokens"] = max_tokens
    if temperature is not None:
        extra["temperature"] = temperature
    return await client.chat.completions.create(
        model=settings.model,
        messages=messages,
        tools=tools or None,
        tool_choice="auto" if tools else None,
        **extra,
    )


async def stream_chat(messages: list[dict]):
    client = get_client()
    stream = await client.chat.completions.create(
        model=settings.model,
        messages=messages,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def stream_with_tools(messages: list[dict], tools: list[dict] | None = None):
    """带工具的流式调用，产出两类事件：

        {"type": "delta", "content": str}            正文增量
        {"type": "tool_calls", "calls": [...]}       本步要调的工具（累积完成）

    为什么要自己写累加器：流式下 tool_calls 是**分片 delta**，同一个 index 的
    arguments 是字符串一段段拼起来的（'{"que' + 'ry":"杭州"}'），只取最后一块
    会拿到半截 JSON。必须按 index 归组、逐段拼接，结束后统一 json.loads。
    """
    client = get_client()
    stream = await client.chat.completions.create(
        model=settings.model,
        messages=messages,
        tools=tools or None,
        tool_choice="auto" if tools else None,
        stream=True,
    )

    pending: dict[int, dict] = {}
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        if delta.content:
            yield {"type": "delta", "content": delta.content}

        for tc in delta.tool_calls or []:
            # index 标识「第几个并行调用」，缺省按 0 处理
            idx = tc.index if tc.index is not None else 0
            slot = pending.setdefault(idx, {"id": "", "name": "", "arguments": ""})
            if tc.id:
                slot["id"] = tc.id
            fn = tc.function
            if fn is None:
                continue
            if fn.name:
                slot["name"] += fn.name
            if fn.arguments:
                slot["arguments"] += fn.arguments

    if pending:
        yield {"type": "tool_calls", "calls": [pending[i] for i in sorted(pending)]}
