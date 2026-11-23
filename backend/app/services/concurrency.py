"""进程内并发闸门：一道身份锁 + 一把全局信号量。

身份锁：登录用户按 user_id、访客按 guest_id 各一把，同一身份串行；
全局信号量：限制整个进程同时执行的 AgentRuntime 任务总数。

信号量是进程级对象，只限制当前进程内的并发；
若用多个 worker 进程部署（如 uvicorn --workers N），每个进程各有一把，
总并发实际为 N × global_concurrency，配置时需注意。
"""

import asyncio
from contextlib import asynccontextmanager

from ..config import settings

# 每次 AgentRuntime 执行都要调 LLM，消耗 token、内存和上游速率配额，
# 请求洪峰无节制并发会打爆进程甚至触发上游限流，因此在这里设总闸。
GLOBAL_SEM = asyncio.Semaphore(settings.global_concurrency)

# 每个身份一把锁。引用计数把等待中的请求也算进去，最后一个离开时才删除，
# 避免锁被提前清掉导致并发串行失效。
_LOCKS: dict[str, tuple[asyncio.Lock, int]] = {}


# 把「含单个 yield 的异步生成器」变成 async with 可用的上下文管理器。
@asynccontextmanager
async def principal_lock(key: str):
    # —— 进入阶段：任何请求（包括正在排队等的）都先把引用计数 +1 ——
    lock, refs = _LOCKS.get(key, (asyncio.Lock(), 0))
    _LOCKS[key] = (lock, refs + 1)
    try:
        async with lock:
            # —— 执行阶段：锁内的 SSE 生成逻辑在跑 ——
            yield
    finally:
        # —— 退出阶段：引用计数 -1，归零才删除锁 ——
        lock, refs = _LOCKS[key]
        if refs <= 1:
            _LOCKS.pop(key, None)
        else:
            _LOCKS[key] = (lock, refs - 1)