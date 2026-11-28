"""记忆提取队列：入队、抢占、超时重排、完成与失败。

多 worker 并发靠一条 CTE + FOR UPDATE SKIP LOCKED 保证不抢重，
应用层不需要额外加锁。
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select, text as sql_text, update

from ..config import settings
from ..db import SessionLocal
from ..models import MemoryJob, now
from ..roles import OwnerKind
from .memory_scope import memory_enabled_for, owner_kind


def enqueue_memory_job(
    owner_key: str,
    run_id: str,
    conversation_id: str | None,
    priority: int = 0,
) -> str | None:
    """登记一条提取任务；同一 run 只保留一条，显式记住只提高优先级。

    priority：0 表示普通轮次自动提取，10 表示用户明确说了「记住」。
    返回 job_id；不入队时返回 None（调用方无需关心原因）。
    """
    # 没有模型 Key 时提取不可能成功，不入队，避免任务在开发环境堆积
    if not settings.api_key or not memory_enabled_for(owner_key):
        return None

    kind = owner_kind(owner_key)
    db = SessionLocal()
    try:
        if kind == OwnerKind.GUEST:
            # 访客每日次数上限：防止清 Cookie 后无限新建访客白吃模型调用
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            used = db.scalar(
                select(func.count(MemoryJob.id)).where(
                    MemoryJob.owner_key == owner_key,
                    MemoryJob.created_at >= today,
                )
            )
            if int(used or 0) >= settings.guest_memory_daily_limit:
                return None

        # 同一 run 已有任务就不再新建，只可能把优先级抬高（普通 → 显式记住）
        existing = db.scalar(select(MemoryJob).where(MemoryJob.run_id == run_id))
        if existing is not None:
            if priority > existing.priority:
                existing.priority = priority
                db.commit()
            return existing.id

        job = MemoryJob(
            id=str(uuid4()),
            owner_key=owner_key,
            owner_kind=kind,
            run_id=run_id,
            conversation_id=conversation_id,
            priority=priority,
            status="pending",
            run_after=now(),
            created_at=now(),
        )
        db.add(job)
        db.commit()
        return job.id
    finally:
        db.close()


def claim_memory_job(worker_id: str) -> dict[str, Any] | None:
    """Postgres 原子抢任务；没有任务返回 None。

    用一条 SQL 完成「挑选 + 加锁 + 标记运行中」，避免多 worker 抢重：
      FOR UPDATE SKIP LOCKED  选中的行加行锁，其他 worker 直接跳过而不阻塞等待
      ORDER BY priority DESC  显式「记住」的任务先处理
      attempts + 1            抢到即计数，失败重试时据此判断是否超上限
    """
    db = SessionLocal()
    try:
        row = db.execute(
            sql_text(
                """
                -- WITH = 公用表表达式（CTE）：给子查询起个临时名字 picked，
                -- 后面紧跟的 UPDATE 就能像用一张表一样引用它。
                -- 整段是「一条语句」：挑任务 + 加锁 + 改状态，在同一快照内完成，
                -- 多 worker 并发时不会抢到同一条（不需要应用层加锁或重试）。

                WITH picked AS (
                    -- 子查询只负责「选」：挑出当前可执行的一条任务并锁在手里
                    SELECT id
                    FROM memory_jobs
                    WHERE status = 'pending'              -- 只抢待处理的（running/done/failed 不要）
                        AND run_after <= now()               -- 跳还在指数退避等待中的任务
                    ORDER BY priority DESC, created_at    -- priority=10（用户说「记住」）优先；同级按先来后到
                    FOR UPDATE SKIP LOCKED                 -- FOR UPDATE：给这行代码加锁、SKIP LOCKED：无法加锁就跳过（已经被其他事务锁住） ；给选中的行加行锁；别人锁住的直接跳过，不阻塞排队
                    LIMIT 1                                -- 一次只抢一条
                )
                UPDATE memory_jobs j
                SET status = 'running',                    -- 抢到即置为运行中，其他人不会再选中
                    locked_at = now(),                     -- 记录加锁时间，供 requeue_stale_jobs 判定僵尸任务
                    locked_by = :worker_id,                -- 记录哪个 worker 在处理，便于排查与人工干预
                    attempts = attempts + 1                -- 抢到就计数，失败重试时据此判断是否超上限
                FROM picked                                -- 只更新 CTE 里选中的那一行（等价于按 id 过滤）
                WHERE j.id = picked.id
                RETURNING j.id, j.owner_key, j.owner_kind, j.run_id,
                          j.conversation_id, j.attempts, j.priority
                          -- RETURNING：把任务内容随更新结果一起带回 Python，省一次 SELECT
                """
            ),
            {"worker_id": worker_id},
        ).mappings().first()
        db.commit()
        return dict(row) if row else None
    finally:
        db.close()


def requeue_stale_jobs(minutes: int = 10) -> int:
    """worker 崩溃后，把长时间卡在 running 的任务放回 pending。"""
    db = SessionLocal()
    try:
        result = db.execute(
            update(MemoryJob)
            .where(
                MemoryJob.status == "running",
                # 返回一段长度为 minutes 分钟的时间间隔
                # now() - timedelta(minutes=minutes) 得到 10 分钟前的时间
                # 总结：找到 running 状态中 locked_at 早于 10 分钟前端的 job
                MemoryJob.locked_at < now() - timedelta(minutes=minutes),
            )
            .values(status="pending", locked_at=None, locked_by=None, run_after=now())
        )
        db.commit()
        return int(result.rowcount or 0)
    finally:
        db.close()


def finish_memory_job(job_id: str, result: str, stats: dict | None = None) -> None:
    """标记任务结束。

    result 记录结论：written（有新写入）/ no_change（只是强化或重复）/
    empty（模型没提取出东西）/ skipped（开关关闭或无用户消息）。
    """
    db = SessionLocal()
    try:
        db.execute(
            update(MemoryJob)
            .where(MemoryJob.id == job_id)
            .values(status="done", result=result, stats=stats or {}, processed_at=now())
        )
        db.commit()
    finally:
        db.close()


def fail_memory_job(
    job_id: str,
    error: str,
    attempts: int,
    *,
    force: bool = False,
    result: str | None = None,
) -> None:
    """失败处理：未达上限则指数退避重排，达到上限标记 failed。

    force=True 用于“模型输出结构始终不合法”这类重试也不会好的情况：
    直接 failed，避免三次盲重试。
    """
    db = SessionLocal()
    try:
        if force or attempts >= settings.memory_max_attempts:
            status = "failed"
            run_after = now()
        else:
            status = "pending"
            run_after = now() + timedelta(seconds=min(300, 5 * (2 ** attempts)))
        db.execute(
            update(MemoryJob)
            .where(MemoryJob.id == job_id)
            .values(
                status=status,
                result=result if status == "failed" else None,
                last_error=error[:1000],
                run_after=run_after,
                locked_at=None,
                locked_by=None,
            )
        )
        db.commit()
    finally:
        db.close()