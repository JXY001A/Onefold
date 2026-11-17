"""DeepSeek（OpenAI 兼容）客户端。"""

from openai import AsyncOpenAI

from ..config import settings


def get_client() -> AsyncOpenAI:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set")
    return AsyncOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )


async def chat(messages: list[dict], tools: list[dict] | None = None):
    client = get_client()
    return await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        tools=tools or None,
        tool_choice="auto" if tools else None,
    )


async def stream_chat(messages: list[dict]):
    client = get_client()
    stream = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
