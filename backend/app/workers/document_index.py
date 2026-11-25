"""文档索引 worker：轮询 document_jobs，解析/分块/embedding/写 chunks。

独立进程运行：
    python -m app.workers.document_index
不接收 HTTP，不与 Web 进程共享内存；所有协调都通过 PostgreSQL。

拆分说明：
    services/document_jobs.py  任务队列（抢单 / 完成 / 失败重试 / 僵尸回收）
    rag/indexer.py             单份文档的解析与建索引
    workers/runner.py          进程骨架（线程数、信号、收尾）
    本文件                     单条任务处理与轮询循环
"""

import logging
import threading
import time

from ..config import settings
from ..db import SessionLocal
from ..rag.indexer import index_document
from ..services.document_jobs import (
    claim_document_job,
    fail_document_job,
    finish_document_job,
    requeue_stale_document_jobs,
)
from ..services.document_store import cleanup_expired
from .runner import run_worker_process

logger = logging.getLogger("onefold.index_worker")

POLL_S = 2.0  # 没抢到任务时的轮询间隔
CLEANUP_INTERVAL_S = 300  # 过期临时文档的清理间隔


def cleanup_expired_documents() -> None:
    """清理过期临时文档，避免长期堆积拖慢索引。"""
    with SessionLocal() as db:
        removed = cleanup_expired(db)
    if removed:
        logger.info("removed %s expired documents", removed)


def process_job(job: dict[str, str]) -> None:
    """建索引；失败交给队列层决定重试还是终结。"""
    try:
        index_document(job["document_id"], job["owner_key"])
    except Exception as exc:  # noqa: BLE001
        logger.exception("index document failed: %s", job["document_id"])
        fail_document_job(job["id"], exc)
    else:
        finish_document_job(job["id"])


def worker_loop(worker_id: str, stop_event: threading.Event) -> None:
    """单个 worker 线程：定期清理过期文档 → 抢任务 → 处理 → 没任务睡一会。

    worker_id 由 runner 传入（用于线程命名）；索引任务不区分 worker，故未使用。
    """
    last_cleanup = 0.0
    while not stop_event.is_set():
        if time.monotonic() - last_cleanup > CLEANUP_INTERVAL_S:
            cleanup_expired_documents()
            # 更新 last_cleanup 时机：确保至少间隔 CLEANUP_INTERVAL_S 调用一次
            # 单调时钟，不可回溯
            last_cleanup = time.monotonic()

        job = claim_document_job()
        if job is None:
            stop_event.wait(POLL_S)
            continue
        process_job(job)


def main() -> None:
    """启动固定数量的 worker 线程；SIGTERM 时停止抢新任务。"""
    run_worker_process(
        name="index-worker",
        loop=worker_loop,
        concurrency=settings.index_worker_concurrency,
        requeue_stale=requeue_stale_document_jobs,
    )


if __name__ == "__main__":
    main()