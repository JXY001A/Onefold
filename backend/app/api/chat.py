"""聊天 SSE（骨架）：排队 → Runtime → 事件流。"""

import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..agent.runtime import AgentRuntime
from ..config import settings

router = APIRouter()

GLOBAL_SEM = asyncio.Semaphore(settings.global_concurrency)
_USER_LOCKS: dict[str, asyncio.Lock] = {}


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    user_id: str | None = None


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(body: ChatRequest):
    async def gen():
        run_id = str(uuid4())
        user_key = body.user_id or "guest"
        lock = _USER_LOCKS.setdefault(user_key, asyncio.Lock())

        try:
            async with lock:
                try:
                    await asyncio.wait_for(
                        GLOBAL_SEM.acquire(), timeout=settings.queue_timeout_s
                    )
                except asyncio.TimeoutError:
                    yield _sse(
                        "error",
                        {"code": "queue_timeout", "message": "排队超时，请稍后再试"},
                    )
                    return

                try:
                    yield _sse("queue", {"position": 0})
                    yield _sse("meta", {"run_id": run_id, "model": settings.deepseek_model})
                    async for event in AgentRuntime().run(
                        query=body.message,
                        user_id=body.user_id,
                        session_id=body.conversation_id,
                    ):
                        yield _sse(event["type"], event["data"])
                finally:
                    GLOBAL_SEM.release()
        except asyncio.CancelledError:
            # 客户端断开：Runtime 的生成器会被取消
            raise

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    # TODO: 按 run_id 找到 asyncio.Task 并 cancel
    return {"ok": True, "run_id": run_id, "note": "TODO"}
