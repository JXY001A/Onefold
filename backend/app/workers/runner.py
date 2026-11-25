"""worker 进程骨架：建表 → 回收僵尸任务 → 起固定数量线程 → 收到信号后收尾。

记忆 worker 与文档索引 worker 只有「单条任务怎么处理」不同，
进程生命周期（线程数、信号、join 超时）完全一致，统一放在这里。
"""

import logging
import signal
import threading
import time
from typing import Callable

from ..db import init_db

logger = logging.getLogger("onefold.worker")

# 单个 worker 线程的签名：线程名 + 停止信号
WorkerLoop = Callable[[str, threading.Event], None]


def run_worker_process(
    *,
    name: str,
    loop: WorkerLoop,
    concurrency: int,
    requeue_stale: Callable[[], int],
) -> None:
    """启动 worker 进程并阻塞到收到 SIGTERM / SIGINT。"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # 建表兜底（首次部署或新增表时生效；不会改已有列结构）
    init_db()

    # 进程刚启动时把上次崩溃遗留在 running 状态的任务重新放回队列
    stale = requeue_stale()
    if stale:
        logger.warning("requeued %s stale %s jobs", stale, name)

    # 停止信号：所有线程都在等它，置位后各线程在下一次循环退出
    stop_event = threading.Event()

    def _stop(*_args) -> None:
        logger.info("%s shutting down", name)
        stop_event.set()

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    # daemon=True：主线程退出时不阻塞进程结束
    threads = [
        threading.Thread(
            target=loop,
            args=(f"{name}-{i + 1}", stop_event),
            daemon=True,
            name=f"{name}-{i + 1}",
        )
        for i in range(max(1, concurrency))
    ]
    for thread in threads:
        thread.start()
    logger.info("%s started: %s threads", name, len(threads))

    # 主线程只做守护：每秒检查一次停止信号
    try:
        while not stop_event.is_set():
            time.sleep(1)
    finally:
        # 给在途任务 30s 收尾时间，超时则随进程一起退出
        for thread in threads:
            thread.join(timeout=30)