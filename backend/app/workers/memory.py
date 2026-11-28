"""长期记忆 worker：轮询 memory_jobs，调 DeepSeek 提取，写 memory_items。

独立进程运行：
    python -m app.workers.memory
不接收 HTTP，不与 Web 进程共享内存；所有协调都通过 PostgreSQL。

拆分说明：
    memory_schema.py   输出契约（Pydantic 模型 + prompt）
    memory_extract.py  单次提取（调模型 + schema 修复）
    runner.py          进程骨架（线程数、信号、收尾）
    本文件             任务处理与轮询循环
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from ..config import settings
from ..services.memory import (
    apply_extraction,
    claim_memory_job,
    fail_memory_job,
    finish_memory_job,
    memory_enabled_for,
    requeue_stale_jobs,
    run_turns,
)
from .memory_extract import extract as _extract
from .memory_schema import CardOp, ExtractionResult, MemorySchemaError, NoteOp
from .runner import run_worker_process

logger = logging.getLogger("onefold.memory_worker")

__all__ = [
    "CardOp",
    "ExtractionResult",
    "MemorySchemaError",
    "NoteOp",
    "main",
    "process_job",
    "worker_loop",
]


def process_job(job: dict[str, Any]) -> None:
    """处理一条 job；空结果、重复、成功、失败分别落到不同 result。

    skipped：开关已关闭 / 没有用户发言
    empty：模型没提取出有价值的记忆
    written：有新写入或更新
    no_change：只是强化计数或命中重复，数据没实质变化
    """
    owner_key = job["owner_key"]
    # 该用户记忆开关是否被关闭
    if not memory_enabled_for(owner_key):
        finish_memory_job(job["id"], "skipped", {"reason": "memory_disabled"})
        return

    # 获取当前会话前面的 memory_max_turns 轮会话
    turns = run_turns(job["run_id"], settings.memory_max_turns)
    user_turns = [t for t in turns if t["role"] == "user"]
    if not user_turns:
        finish_memory_job(job["id"], "skipped", {"reason": "no_turns"})
        return

    # 白名单：只有用户本人说过的话才能作为证据
    allowed_ids = {t["id"] for t in user_turns}

    # 调用模型提取记忆
    result = _extract(owner_key, turns, int(job.get("priority") or 0))

    # 只保留有用户证据的候选；模型编造或引用了助手/工具消息的 message id 直接丢弃
    cards = [
        c.model_dump()
        for c in result.cards[: settings.memory_extract_max_cards]
        if c.source_message_id in allowed_ids
    ]
    notes = [
        n.model_dump()
        for n in result.notes[: settings.memory_extract_max_notes]
        if n.source_message_id in allowed_ids
    ]

    if not cards and not notes:
        finish_memory_job(job["id"], "empty", {"cards": 0, "notes": 0})
        return

    # 落库：新增/更新卡片、写入笔记、重复则强化 mention_count
    stats = apply_extraction(owner_key, job["run_id"], cards, notes)
    # 有实质写入才算 written，否则降级为 no_change / empty，便于统计口径区分
    if stats.get("added", 0) or stats.get("updated", 0) or stats.get("notes", 0):
        result_name = "written"
    elif stats.get("reinforced", 0) or stats.get("duplicates", 0):
        result_name = "no_change"
    else:
        result_name = "empty"
    finish_memory_job(job["id"], result_name, stats)


# 数据库瞬时故障（如连接被管理员切断、数据库重启）后的退避秒数。
# 领取任务阶段出错必须退避重试，绝不能让线程退出（2026-11-28 线上事故）。
RETRY_WAIT_S = 5.0


# 参数都在线程启动的时候传入的
def worker_loop(worker_id: str, stop_event: threading.Event) -> None:
    """单个 worker 线程：抢任务 → 处理 → 没任务睡一会。"""
    # 没有收到程序终止信号，继续循环
    while not stop_event.is_set():
        try:
            # 抢任务
            job = claim_memory_job(worker_id)
            if job is None:
                # 没任务就 sleep 一下，避免 CPU 占用过高
                stop_event.wait(settings.memory_poll_s)
                continue
            # 处理任务
            try:
                process_job(job)
            except MemorySchemaError as exc:
                # 模型两次都输出错字段，重试同一 prompt 也不会好；直接 failed 供排查
                logger.exception("memory job %s invalid schema", job.get("id"))
                fail_memory_job(
                    job["id"],
                    f"{type(exc).__name__}: {exc}",
                    int(job.get("attempts") or 1),
                    force=True,
                    result="invalid_schema",
                )
            # 处理失败就重试
            except Exception as exc:  # noqa: BLE001
                logger.exception("memory job %s failed", job.get("id"))
                fail_memory_job(job["id"], f"{type(exc).__name__}: {exc}", int(job.get("attempts") or 1))
        except Exception:  # noqa: BLE001
            # 领取任务 / 失败落账阶段的数据库异常：退避后继续，不能打死线程
            logger.exception("memory worker loop error; retry in %ss", RETRY_WAIT_S)
            stop_event.wait(RETRY_WAIT_S)


def main() -> None:
    """启动固定数量的 worker 线程；SIGTERM 时停止抢新任务。"""
    run_worker_process(
        name="memory-worker",
        loop=worker_loop,
        concurrency=settings.memory_worker_concurrency,
        requeue_stale=requeue_stale_jobs,
    )


if __name__ == "__main__":
    main()