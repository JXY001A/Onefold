"""聊天 SSE 接口。

整体流程：
    请求进入 → 获取身份锁（同一用户/访客串行）
            → 带超时地获取全局信号量（跨用户总并发限制，排队超时则返回错误事件）
            → 调用 AgentRuntime 执行 → 以 SSE 事件流逐步返回结果。

并发控制采用「身份锁 + 全局信号量」双层结构，实现见 services/concurrency。
一轮结束后的落库与后续任务见 services/run_finalizer。
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..agent.runtime import AgentRuntime
from ..config import settings
from ..services.concurrency import GLOBAL_SEM, principal_lock
from ..services.history import (
    conversation_owned_by,
    create_run,
    get_or_create_conversation,
)
from ..services.memory import get_memory_snapshot
from ..services.quota import rounds_used
from ..services.run_finalizer import finalize_run
from .deps import Principal, current_principal
from .sse import event_stream, sse_event

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    # 本次用户输入的消息内容（必填）
    message: str
    # 会话 ID：多轮对话时沿用同一 ID 以关联上下文，单轮对话可省略
    conversation_id: str | None = None


@router.post("/chat")
async def chat(
    body: ChatRequest,
    # FastAPI 看到 Depends(current_principal) 会先执行它，把身份对象注入 principal，
    # 函数体里不需要写任何鉴权代码就能拿到「当前请求是谁」。
    principal: Principal = Depends(current_principal),
):
    """聊天入口：立即返回 StreamingResponse，真正的处理逻辑在异步生成器 gen() 中。

    注意：chat 本身不执行任何并发控制——所有排队、限流逻辑都发生在
    gen() 内部。因为 FastAPI/Starlette 只有在客户端开始消费响应体时
    才会驱动生成器执行，这意味着并发控制的生效时机被推迟到了
    「客户端真正开始接收流」的时刻。
    """

    # 归属校验：回传 conversation_id 时，该会话必须属于当前身份。
    # 登录用户与访客统一走 owner_key（"user:<id>" / "guest:<id>"），不再为访客单独开叉：
    # 访客同样可以拥有多个会话，越权判断只看归属，不看身份类型。
    if body.conversation_id and not conversation_owned_by(
        body.conversation_id, principal.owner_key
    ):
        raise HTTPException(403, "无权访问该会话")

    # 游客配额：一轮 = 一次「提问 → 回答结束」，即后建的一条 run；用完必须注册。
    # 放在建 run 之前计数，超限时不会多出一条 run。登录用户不限量。
    if (
        principal.role == "guest"
        and rounds_used(principal.owner_key) >= settings.guest_max_rounds
    ):
        raise HTTPException(
            403, f"免费体验 {settings.guest_max_rounds} 轮已用完，注册后继续"
        )

    async def gen():
        # 会话 ID 在拿到许可后才确定：不传则新建（标题取首条消息），传入则刷新活跃时间。
        # 放在排队之后，避免排队超时的请求在白建一条会话记录。
        try:
            async with principal_lock(principal.lock_key):
                # —— 第一道闸已通过：此刻该身份只有本请求在执行 ——
                # —— 第二道闸：全局信号量，带排队超时 ——
                # 排队是异步等待：让出控制权、不占 CPU，其他请求仍能被处理。
                # 超时时 wait_for 会取消内部的 acquire 任务，并未拿到许可，
                # 因此无需也不应 release，信号量计数不会泄漏。
                try:
                    await asyncio.wait_for(
                        GLOBAL_SEM.acquire(), timeout=settings.queue_timeout_s
                    )
                except asyncio.TimeoutError:
                    yield sse_event(
                        "error",
                        {"code": "queue_timeout", "message": "排队超时，请稍后再试"},
                    )
                    return

                # —— 两道闸均已通过：获得执行资格，进入真正的执行阶段 ——
                # 本轮运行状态：默认 error；正常走完改 done；客户端断开改 cancelled。
                status = "error"

                # 会话/运行 ID 在数据库写入成功后才确定；提前声明便于 finally 使用
                conversation_id: str | None = None
                run_id: str | None = None

                # 本轮运行器：落库时读它的 transcript（含 user / assistant / tool 三步）
                runtime: AgentRuntime | None = None
                try:
                    # 定位/新建会话（后端生成 ID，并通过 meta 事件下发，前端后续轮次回传复用），
                    # 再建本轮 run：消息通过 run_id 归属到会话。
                    conversation_id = get_or_create_conversation(
                        owner_key=principal.owner_key,
                        conversation_id=body.conversation_id,
                        title_seed=body.message,
                    )

                    run_id = create_run(principal.user_id, conversation_id)

                    # 会话级记忆快照：整个会话复用，worker 更新记忆不影响进行中的对话
                    try:
                        memory_snapshot = get_memory_snapshot(
                            conversation_id, principal.owner_key, body.message
                        )
                    except Exception:
                        logger.exception("load memory snapshot failed: %s", conversation_id)
                        memory_snapshot = ""

                    # 通知前端已开始执行。position 恒为 0 是骨架实现：
                    # 只有拿到许可才会走到这里，等价于已排到队首；
                    # 后续若实现真实队列，可改为真实的排队位置。
                    yield sse_event("queue", {"position": 0})

                    # 下发元信息：run_id 供前端关联/取消；conversation_id 供登录用户首轮存下，
                    # 后续轮次作为 conversation_id 回传，历史才能接上。
                    yield sse_event(
                        "meta",
                        {
                            "run_id": run_id,
                            "model": settings.model,
                            "conversation_id": conversation_id,
                        },
                    )
                    # 驱动 AgentRuntime 执行：它自己按需加载历史（含工具步骤），
                    # 并把每个内部事件原样转成 SSE 下发。执行时长不受 wait_for 限制。
                    runtime = AgentRuntime()
                    async for event in runtime.run(
                        query=body.message,
                        run_id=run_id,
                        owner_key=principal.owner_key,
                        user_id=principal.user_id,
                        conversation_id=conversation_id,
                        memory_text=memory_snapshot,
                    ):
                        yield sse_event(event["type"], event["data"])
                    status = "done"
                except asyncio.CancelledError:
                    # 客户端中途断开：已生成的部分回答照样保留，run 标记为 cancelled
                    status = "cancelled"
                    raise
                finally:
                    # 无论正常结束、抛出异常还是被取消，都必须归还全局许可，
                    # 否则信号量计数被耗尽，后续请求将全部排队超时（死锁式的饿死）。
                    GLOBAL_SEM.release()

                    # 落库与后续任务全部交给 run_finalizer：中断/异常时 transcript
                    # 里仍是已完成的部分，下一轮照样能回放。
                    finalize_run(
                        run_id=run_id,
                        status=status,
                        owner_key=principal.owner_key,
                        user_id=principal.user_id,
                        role=principal.role,
                        conversation_id=conversation_id,
                        message=body.message,
                        transcript=list(runtime.transcript) if runtime else [],
                    )

                # 走到这里说明执行正常结束（未超时、未取消）。
                # async with 退出时自动释放身份锁，同一身份的下一个请求得以继续。
        except asyncio.CancelledError:
            # 客户端断开连接时，Starlette 会向生成器抛 CancelledError 取消它：
            # - GLOBAL_SEM.release() 已由上面的 finally 保证执行；
            # - 身份锁由 async with 退出时自动释放；
            # - AgentRuntime 内部的 LLM 调用等异步任务也会随取消链一并取消。
            # 这里捕获后必须原样 re-raise：生成器被取消是响应提前终止的正常机制，
            # 若吞掉 CancelledError，Starlette 会因生成器未真正结束而出现异常行为。
            raise

    # 以流式响应的方式返回生成器。
    return event_stream(gen())


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    """按 run_id 取消正在执行的运行（骨架占位）。

    目前未实现：要真正生效，需要在 chat 的 gen() 中把 AgentRuntime 的执行
    封装成 asyncio.Task，并按 run_id 登记到任务表，此接口再从中查找并 cancel。
    """
    # TODO: 按 run_id 找到 asyncio.Task 并 cancel
    return {"ok": True, "run_id": run_id, "note": "TODO"}