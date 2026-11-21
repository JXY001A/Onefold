"""聊天 SSE 接口（骨架）。

整体流程：
    请求进入 → 获取身份锁（同一用户/访客串行）
            → 带超时地获取全局信号量（跨用户总并发限制，排队超时则返回错误事件）
            → 调用 AgentRuntime 执行 → 以 SSE 事件流逐步返回结果。

并发控制采用「身份锁 + 全局信号量」双层结构：
    - 身份锁：登录用户按 user_id、访客按 guest_id 各一把，同一身份串行；
    - 全局信号量：限制整个服务同时执行的 AgentRuntime 任务总数。
"""

import asyncio
import json
import logging
import re
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..agent.runtime import AgentRuntime
from ..config import settings
from ..services.history import (
    conversation_owned_by,
    create_run,
    finish_run,
    get_or_create_conversation,
    save_transcript,
)
from ..services.memory import enqueue_memory_job, get_memory_snapshot, memory_enabled_for
from ..services.quota import rounds_used
from .deps import Principal, current_principal

logger = logging.getLogger(__name__)
_EXPLICIT_MEMORY = re.compile(r"记住|记一下|别忘|以后都|remember", re.IGNORECASE)

router = APIRouter()

# 全局信号量：限制同时执行 AgentRuntime 的任务总数，上限取自配置 global_concurrency。
# 为什么需要：
#   每次 AgentRuntime 执行都要调用 LLM API，消耗 token、内存和上游速率配额，
#   若请求洪峰无节制地并发执行，会打爆后端进程甚至触发上游限流。
# 作用范围：
#   信号量是进程级对象，只限制当前进程内的并发；
#   若用多个 worker 进程部署（如 uvicorn --workers N），每个进程各有一把，
#   总并发实际为 N × global_concurrency，配置时需注意。
GLOBAL_SEM = asyncio.Semaphore(settings.global_concurrency)

# 每个身份一把锁：登录用户按 user_id，访客按 guest_id。
# 引用计数把等待中的请求也算进去，最后一个离开时才删除，避免锁被提前清掉。
_LOCKS: dict[str, tuple[asyncio.Lock, int]] = {}

# 把「含单个 yield 的异步生成器」变成 async with 可用的上下文管理器。
@asynccontextmanager
async def principal_lock(key: str):
    # —— 进入阶段:任何请求(包括正在排队等的)都先把引用计数 +1 ——
    lock, refs = _LOCKS.get(key, (asyncio.Lock(), 0))
    _LOCKS[key] = (lock, refs + 1)
    try:
        async with lock:
            # —— 执行阶段:锁内的 SSE 生成逻辑在跑 ——
            yield
    finally:
        # —— 退出阶段:引用计数 -1,归零才删除锁 ——
        lock, refs = _LOCKS[key]
        if refs <= 1:
            _LOCKS.pop(key, None)
        else:
            _LOCKS[key] = (lock, refs - 1)


class ChatRequest(BaseModel):
    # 本次用户输入的消息内容（必填）
    message: str
    # 会话 ID：多轮对话时沿用同一 ID 以关联上下文，单轮对话可省略
    conversation_id: str | None = None


def _sse(event: str, data: dict) -> str:
    """把事件类型与数据拼装成一条标准 SSE 消息。

    SSE 协议格式：每条消息由 "event: 类型"、"data: JSON" 两行组成，
    以空行结尾；两条消息之间靠这个空行分隔。
    ensure_ascii=False 保证中文等非 ASCII 字符原样输出，便于前端直接展示。
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(
    body: ChatRequest,
    # 请求到达 /chat 时,FastAPI 看到 Depends(current_principal),会自动执行 current_principal(),把返回的身份对象注入 principal 参数。chat 函数体里不需要写任何鉴权代码,就能直接拿到「当前请求是谁」。
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
                try:
                    # GLOBAL_SEM.acquire() 在做什么：
                    # 信号量内部是一个计数器，初始值为 settings.global_concurrency（如 5）。
                    # 可以把它想成「只有 N 个车位的停车场」：
                    # - acquire() = 进停车场：有空位（计数 > 0）就占一个（计数 -1）并立即返回；
                    #   没空位（计数 == 0）就在门口挂起排队，直到有人 release() 腾出车位。
                    # - release() = 出停车场：腾出一个车位（计数 +1），并唤醒门口队伍里的第一个等待者。
                    # 挂起是「异步等待」：排队期间协程让出控制权，不占 CPU、不阻塞事件循环，
                    # 其他请求仍能正常处理（这正是 async/await 协作式并发的意义）。
                    #
                    # 若直接 await GLOBAL_SEM.acquire() 不加限制，排队是无限期的；
                    # 因此用 wait_for 加上超时：排队超过 queue_timeout_s 秒仍未拿到许可，
                    # 就放弃等待、向前端返回 queue_timeout 错误，避免请求无限悬挂。
                    # 超时发生时 wait_for 会取消内部的 acquire 任务，
                    # 被取消的 acquire 并未拿到许可，因此无需也不应 release，
                    # 信号量计数不会泄漏。
                    await asyncio.wait_for(
                        GLOBAL_SEM.acquire(), timeout=settings.queue_timeout_s
                    )
                except asyncio.TimeoutError:
                    yield _sse(
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

                    yield _sse("queue", {"position": 0})
                    
                    # 下发元信息：run_id 供前端关联/取消；conversation_id 供登录用户首轮存下，
                    # 后续轮次作为 conversation_id 回传，历史才能接上。
                    
                    yield _sse(
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
                        yield _sse(event["type"], event["data"])
                    status = "done"
                except asyncio.CancelledError:
                    # 客户端中途断开：已生成的部分回答照样保留，run 标记为 cancelled
                    status = "cancelled"
                    raise
                finally:
                    # 无论正常结束、抛出异常还是被取消，都必须归还全局许可，
                    # 否则信号量计数被耗尽，后续请求将全部排队超时（死锁式的饿死）。
                    # 放在 finally 里是信号量正确性的关键。
                    GLOBAL_SEM.release()
                    
                    # 落库：把本轮完整 transcript（user + assistant + tool）一次写入。
                    # 中断/异常时 transcript 里仍是已完成的部分，下一轮照样能回放。
                    # 注：这里是同步数据库写（毫秒级）；QPS 上来后可改
                    # asyncio.to_thread 或投递到真正的写入队列。
                    if run_id:
                        saved = list(runtime.transcript) if runtime else []
                        if not saved:
                            # 还没进 runtime 就失败/取消了：至少把用户问题留下
                            saved = [{"role": "user", "content": body.message}]
                        save_transcript(run_id, saved)
                        finish_run(run_id, status)

                        # 记忆提取只登记任务，绝不阻塞本轮回答；失败也不影响聊天
                        guest_ready = (
                            principal.role == "guest"
                            and rounds_used(principal.owner_key) >= settings.guest_memory_min_rounds
                        )
                        if status == "done" and conversation_id and (
                            principal.role == "user" or guest_ready
                        ):
                            try:
                                if memory_enabled_for(principal.owner_key):
                                    enqueue_memory_job(
                                        owner_key=principal.owner_key,
                                        run_id=run_id,
                                        conversation_id=conversation_id,
                                        priority=10 if _EXPLICIT_MEMORY.search(body.message) else 0,
                                    )
                            except Exception:
                                logger.exception("enqueue memory job failed: run=%s", run_id)

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
    return StreamingResponse(
        gen(),
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


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    """按 run_id 取消正在执行的运行（骨架占位）。

    目前未实现：要真正生效，需要在 chat 的 gen() 中把 AgentRuntime 的执行
    封装成 asyncio.Task，并按 run_id 登记到任务表，此接口再从中查找并 cancel。
    """
    # TODO: 按 run_id 找到 asyncio.Task 并 cancel
    return {"ok": True, "run_id": run_id, "note": "TODO"}
