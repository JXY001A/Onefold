"""SSE 事件组装与流式响应封装。

SSE 协议格式：每条消息由 "event: 类型"、"data: JSON" 两行组成，
以空行结尾；两条消息之间靠这个空行分隔。
"""

import json
from typing import AsyncGenerator

from fastapi.responses import StreamingResponse


def sse_event(event: str, data: dict) -> str:
    """把事件类型与数据拼装成一条标准 SSE 消息。

    ensure_ascii=False 保证中文等非 ASCII 字符原样输出，便于前端直接展示。
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def event_stream(gen: AsyncGenerator[str, None]) -> StreamingResponse:
    """把生成器包装成 SSE 响应，并关掉沿途所有缓存与代理缓冲。"""
    return StreamingResponse(
        gen,
        media_type="text/event-stream",
        headers={
            # 禁止任何中间层缓存 SSE 流
            "Cache-Control": "no-cache",
            # 保持连接：SSE 依赖一条长连接持续推送事件
            "Connection": "keep-alive",
            # 关键：禁用 Nginx 等反向代理的响应缓冲。若不禁用，
            # 代理会把事件攒在缓冲区里不实时下发，前端将收不到流式输出。
            "X-Accel-Buffering": "no",
        },
    )