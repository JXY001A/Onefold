"""文档索引任务队列：抢单、完成、失败重试、僵尸回收。

worker 只负责循环与业务调用，任务状态的全部变更集中在这里，
与 services/memory_jobs.py 保持同一套命名与语义。
"""

import logging
from datetime import timedelta

from sqlalchemy import or_, select

from ..config import settings
from ..db import SessionLocal
from ..models import Document, DocumentJob, now

logger = logging.getLogger(__name__)

STALE_S = 15 * 60  # running 超过该时长，视为进程已崩溃
RETRY_BACKOFF_S = 30  # 每多一次尝试多退避 30s


def claim_document_job() -> dict[str, str] | None:
    """原子抢占一条到点任务；没有任务返回 None。"""
    with SessionLocal() as db:
        stmt = (
            select(DocumentJob)
            .where(
                DocumentJob.status == "pending",
                or_(DocumentJob.run_after.is_(None), DocumentJob.run_after <= now()),
            )
            .order_by(DocumentJob.created_at)
            # SKIP LOCKED：多个 worker 并行时不会抢到同一条
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        job = db.execute(stmt).scalar_one_or_none()
        if job is None:
            return None
        job.status = "running"
        job.started_at = now()
        job.attempts += 1
        job.stage = "parse"
        db.commit()
        return {
            "id": job.id,
            "document_id": job.document_id,
            "owner_key": job.owner_key,
            "attempts": job.attempts,
        }


def finish_document_job(job_id: str) -> None:
    with SessionLocal() as db:
        job = db.get(DocumentJob, job_id)
        if job is None:
            return
        job.status = "done"
        job.stage = "done"
        job.processed_at = now()
        job.finished_at = now()
        db.commit()


def fail_document_job(job_id: str, exc: Exception) -> None:
    """未到重试上限就退避重排，到上限则任务与文档一起置为 failed。"""
    with SessionLocal() as db:
        job = db.get(DocumentJob, job_id)
        if job is None:
            return
        job.last_error = f"{type(exc).__name__}: {str(exc)[:300]}"
        if job.attempts >= settings.index_max_attempts:
            job.status = "failed"
            job.finished_at = now()
            doc = db.get(Document, job.document_id)
            if doc is not None:
                doc.status = "failed"
                doc.error = job.last_error
        else:
            # 指数退避由 attempts 控制，简单可预期
            job.status = "pending"
            job.run_after = now() + timedelta(seconds=RETRY_BACKOFF_S * job.attempts)
        db.commit()


def requeue_stale_document_jobs() -> int:
    """进程崩溃后，把长时间 running 的任务重新放回队列。"""
    with SessionLocal() as db:
        stale = list(db.execute(select(DocumentJob).where(DocumentJob.status == "running")).scalars())
        count = 0
        for job in stale:
            if job.started_at and now() - job.started_at > timedelta(seconds=STALE_S):
                job.status = "pending"
                job.run_after = now()
                count += 1
        db.commit()
        return count