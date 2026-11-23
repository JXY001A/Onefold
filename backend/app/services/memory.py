"""长期记忆读写：入队、读取注入、用户编辑、worker 任务处理。"""

from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select, text as sql_text, update

from ..config import settings
from ..db import SessionLocal
from ..models import (
    Conversation,
    MemoryEvent,
    MemoryItem,
    MemoryJob,
    MemorySetting,
    Message,
    Run,
    now,
)

# 记忆分类：全链路只用中文，写入、注入、界面展示共用这一份定义
CATEGORIES = (
    "身份",  # 姓名、年龄、城市、时区、母语等不变的自我标识
    "职业",  # 公司、职位、行业、从业年限
    "教育",  # 学校、专业、学位、证书
    "技能",  # 语言、框架、工具及熟练度
    "项目",  # 在做或做过的产品、技术选型、进展
    "目标",  # 想达成但还没做到的计划与期限
    "偏好",  # 主观喜欢/讨厌的技术、工具、内容、审美
    "沟通",  # 希望被怎么回答：语言、篇幅、语气
    "习惯",  # 作息、工作流、固定流程
    "关系",  # 家人、同事、合作者及其角色
    "约束",  # 硬规则：禁止事项、必须满足的条件
    "兴趣",  # 工作之外的爱好与关注领域
    "其他",  # 确实无法归类的稳定事实，占比应低于 10%
)

# 历史英文值与模型偶发别名的兼容映射；未知值统一降级为「其他」
CATEGORY_ALIASES = {
    "profile": "身份",
    "identity": "身份",
    "personal": "身份",
    "career": "职业",
    "occupation": "职业",
    "job": "职业",
    "work": "职业",
    "education": "教育",
    "skill": "技能",
    "skills": "技能",
    "project": "项目",
    "projects": "项目",
    "goal": "目标",
    "goals": "目标",
    "plan": "目标",
    "preference": "偏好",
    "preferences": "偏好",
    "communication": "沟通",
    "style": "沟通",
    "habit": "习惯",
    "habits": "习惯",
    "routine": "习惯",
    "relationship": "关系",
    "relationships": "关系",
    "people": "关系",
    "constraint": "约束",
    "constraints": "约束",
    "rule": "约束",
    "interest": "兴趣",
    "interests": "兴趣",
    "hobby": "兴趣",
    "other": "其他",
    "misc": "其他",
}


def normalize_category(raw: str | None) -> str:
    """把任意来源的分类值归一成 CATEGORIES 里的中文值。

    模型输出、历史英文数据、注入标签都走这里，保证只有一个真源；
    认不出的值一律落到「其他」，不让脏值进库，也不让注入时显示成英文。
    """
    value = str(raw or "").strip()
    if value in CATEGORIES:
        return value
    return CATEGORY_ALIASES.get(value.lower(), "其他")


def _owner_kind(owner_key: str) -> str:
    """从 user:<id> / guest:<id> 取身份类型。"""
    return "guest" if owner_key.startswith("guest:") else "user"


def _normalize(text: str) -> str:
    """指纹归一化：小写 + 压缩空白。"""
    return " ".join(str(text or "").lower().split())


def _fingerprint(text: str) -> str:
    """笔记去重指纹：归一化后取 sha256，同一句话换种写法也能判重。

    只用于 note（没有 key 的自由文本）；card 靠 category + key 判重。
    """
    return hashlib.sha256(_normalize(text).encode("utf-8")).hexdigest()


def _recency(value: datetime | None) -> float:
    """30 天半衰的新鲜度，返回 0~1。"""
    if value is None:
        return 0.0
    current = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    days = max(0.0, (datetime.now(timezone.utc) - current).total_seconds() / 86400)
    return math.exp(-math.log(2) * days / 30)


def _log_weight(count: int | None, cap: int = 10) -> float:
    """把次数压成 0~1；第 10 次以后趋平，避免刷屏霸榜。"""
    return min(1.0, math.log1p(max(0, count or 0)) / math.log1p(cap))


def _terms(text: str) -> set[str]:
    """轻量检索词：英文/数字词 + 中文二元组，够小数据量用。"""
    lowered = (text or "").lower()
    ascii_words = set(re.findall(r"[a-z0-9_]{2,}", lowered))
    han = re.findall(r"[\u4e00-\u9fff]", lowered)
    bigrams = {han[i] + han[i + 1] for i in range(len(han) - 1)}
    return ascii_words | bigrams


def _relevance(query: str, text: str) -> float:
    """0~1 的相关性：整句包含直接给 1，否则按词重合比例。"""
    if not query or not text:
        return 0.0
    q = query.lower()
    t = text.lower()
    if q in t:
        return 1.0
    query_terms = _terms(query)
    if not query_terms:
        return 0.0
    return len(query_terms & _terms(text)) / len(query_terms)


def memory_enabled_for(owner_key: str) -> bool:
    """两级开关：全局配置与单用户设置都为真才启用。

    用户没建过 settings 行时默认开启，省掉首次写库。
    """
    if not settings.memory_enabled:
        return False
    db = SessionLocal()
    try:
        row = db.get(MemorySetting, owner_key)
        return row.enabled if row else True
    finally:
        db.close()


def set_memory_enabled(owner_key: str, enabled: bool) -> None:
    """写入单用户开关：已有记录就更新，没有就新建一行。"""
    db = SessionLocal()
    try:
        row = db.get(MemorySetting, owner_key)
        if row is None:
            row = MemorySetting(owner_key=owner_key, enabled=enabled, updated_at=now())
            db.add(row)
        else:
            row.enabled = enabled
            row.updated_at = now()
        db.commit()
    finally:
        db.close()


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

    owner_kind = _owner_kind(owner_key)
    db = SessionLocal()
    try:
        if owner_kind == "guest":
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
            owner_kind=owner_kind,
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


def run_turns(run_id: str, max_turns: int = 10) -> list[dict[str, str]]:
    """读取截至当前 run 的最近对话，只保留 user / assistant。

    用 started_at <= 当前 run 定位，保证能拿到跨多个 run 的上下文；
    tool 角色的消息不参与提取（工具输出不能当作事实）。
    """
    db = SessionLocal()
    try:
        current = db.get(Run, run_id)
        if current is None or current.started_at is None:
            return []
        runs = db.execute(
            select(Run)
            .where(
                Run.conversation_id == current.conversation_id,
                Run.started_at <= current.started_at,
            )
            .order_by(Run.started_at.desc())
            .limit(max_turns)
        ).scalars().all()
        run_ids = [r.id for r in runs]
        if not run_ids:
            return []
        rows = db.execute(
            select(Message)
            # 使用 in 逻辑找到有效的 message 
            .where(Message.run_id.in_(run_ids), Message.role.in_(("user", "assistant")))
            .order_by(Message.created_at, Message.seq)
        ).scalars().all()
        return [
            {"id": m.id, "run_id": m.run_id, "role": m.role, "content": m.content}
            for m in rows
        ]
    finally:
        db.close()


def message_is_user_evidence(run_id: str, message_id: str) -> bool:
    """防止模型把助手的话/搜索结果当作用户事实。"""
    db = SessionLocal()
    try:
        row = db.scalar(
            select(Message).where(
                Message.id == message_id,
                Message.run_id == run_id,
                Message.role == "user",
            )
        )
        return row is not None
    finally:
        db.close()


def _record_event(
    db,
    owner_key: str,
    owner_kind: str,
    memory_id: str | None,
    action: str,
    old_value: dict | None,
    new_value: dict | None,
    source_run_id: str | None,
    actor: str = "worker",
) -> None:
    """写一条变更审计（不单独提交，跟着调用方的事务一起落库）。

    actor：worker = 模型自动提取，user = 用户手动编辑/删除。
    只 add 到 session，由外层统一 commit，保证业务改动与审计记录同生共死。
    """
    db.add(
        MemoryEvent(
            id=str(uuid4()),
            owner_key=owner_key,
            owner_kind=owner_kind,
            memory_id=memory_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            source_run_id=source_run_id,
            actor=actor,
            created_at=now(),
        )
    )


def apply_extraction(
    owner_key: str,
    run_id: str,
    cards: list[dict[str, Any]],
    notes: list[dict[str, Any]],
) -> dict[str, int]:
    """把 worker 校验后的 cards/notes 写入数据库；同一事务完成。

    两类记忆的去重与写入规则不同：
      card  以 (category, key) 为唯一键：不存在则新增；值相同则只强化计数；
            值不同则覆盖并记一条 update 审计（用户偏好变了）。
      note  以文本指纹去重：命中则强化计数，不重复写入。
    """
    owner_kind = _owner_kind(owner_key)
    stats = {"added": 0, "updated": 0, "reinforced": 0, "notes": 0, "duplicates": 0}
    db = SessionLocal()
    try:
        for card in cards:
            # 分类先归一再入库：(category, key) 是判重键，英文/中文混写会拆成两条
            category = normalize_category(card.get("category"))
            key = str(card["key"])
            value = card.get("value")
            existing = db.scalar(
                select(MemoryItem).where(
                    MemoryItem.owner_key == owner_key,
                    MemoryItem.kind == "card",
                    MemoryItem.category == category,
                    MemoryItem.key == key,
                    MemoryItem.status == "active",
                )
            )
            if existing is None:
                row = MemoryItem(
                    id=str(uuid4()),
                    owner_key=owner_key,
                    owner_kind=owner_kind,
                    kind="card",
                    category=category,
                    key=key,
                    value=value,
                    text=str(card["text"]),
                    confidence=float(card.get("confidence", 0.8)),
                    mention_count=1,
                    usage_count=0,
                    source_run_id=run_id,
                    source_message_id=card.get("source_message_id"),
                    last_mentioned_at=now(),
                    status="active",
                    created_at=now(),
                    updated_at=now(),
                )
                db.add(row)
                _record_event(db, owner_key, owner_kind, row.id, "add", None, {"value": value, "text": row.text}, run_id)
                stats["added"] += 1
                continue

            if existing.value == value:
                # 同一事实被重复提醒：只强化，不新增
                existing.mention_count += 1
                existing.last_mentioned_at = now()
                existing.confidence = max(existing.confidence, float(card.get("confidence", 0.8)))
                existing.updated_at = now()
                stats["reinforced"] += 1
            else:
                old = {"value": existing.value, "text": existing.text}
                existing.value = value
                existing.text = str(card["text"])
                existing.confidence = float(card.get("confidence", 0.8))
                existing.mention_count = 1
                existing.source_run_id = run_id
                existing.source_message_id = card.get("source_message_id")
                existing.last_mentioned_at = now()
                existing.updated_at = now()
                _record_event(db, owner_key, owner_kind, existing.id, "update", old, {"value": value, "text": existing.text}, run_id)
                stats["updated"] += 1

        for note in notes:
            # 唯一键：文本指纹：可以理解为针对这段文本生成了唯一一个指纹，文本不变则指纹相同
            text_value = str(note["text"])
            fp = _fingerprint(text_value)
            existing = db.scalar(
                select(MemoryItem).where(
                    MemoryItem.owner_key == owner_key,
                    MemoryItem.kind == "note",
                    MemoryItem.fingerprint == fp,
                    MemoryItem.status == "active",
                )
            )
            if existing is not None:
                existing.mention_count += 1
                existing.last_mentioned_at = now()
                existing.confidence = max(existing.confidence, float(note.get("confidence", 0.8)))
                existing.updated_at = now()
                stats["duplicates"] += 1
                continue
            row = MemoryItem(
                id=str(uuid4()),
                owner_key=owner_key,
                owner_kind=owner_kind,
                kind="note",
                category=normalize_category(note.get("category")),
                key=None,
                value=None,
                text=text_value,
                fingerprint=fp,
                confidence=float(note.get("confidence", 0.8)),
                mention_count=1,
                usage_count=0,
                source_run_id=run_id,
                source_message_id=note.get("source_message_id"),
                happened_at=note.get("happened_at"),
                last_mentioned_at=now(),
                status="active",
                created_at=now(),
                updated_at=now(),
            )
            db.add(row)
            _record_event(db, owner_key, owner_kind, row.id, "add", None, {"text": text_value}, run_id)
            stats["notes"] += 1

        db.commit()
        return stats
    finally:
        db.close()


def _card_score(item: MemoryItem) -> float:
    """卡片排序权重（不依赖 query）：固定 > 置信度高 > 新近 > 被多次提到/使用。"""
    return (
        # pinned ：被用户强调记住的
        0.30 * (1.0 if item.pinned else 0.0)
        # confidence 可信度
        + 0.20 * max(0.0, min(1.0, item.confidence))
        # 上次被提及  或 最近更新时间
        + 0.15 * _recency(item.last_mentioned_at or item.updated_at)
        # mention_count 提及次数
        + 0.20 * _log_weight(item.mention_count)
        # usage_count 使用次数
        + 0.15 * _log_weight(item.usage_count)
    )


def _note_score(item: MemoryItem, query: str) -> float:
    """笔记排序权重：与当前问题相关占一半，其余看置信度、新近与使用频率。"""
    return (
        0.50 * _relevance(query, item.text)
        + 0.15 * max(0.0, min(1.0, item.confidence))
        + 0.10 * _recency(item.last_mentioned_at or item.updated_at)
        + 0.15 * _log_weight(item.mention_count)
        + 0.10 * _log_weight(item.usage_count)
    )


def load_memory_context(owner_key: str, query: str) -> str:
    """读取并渲染注入文本；没有记忆/关闭时返回空串。

    筛选顺序：
      1. 卡片按 _card_score 排序，同类目最多 8 条、总数受 memory_cards_max 限制
      2. 笔记只保留与当前问题相关的（_relevance > 0），取前 memory_notes_max 条
      3. 超预算时先丢笔记，再丢低分卡片（按 4 字符 ≈ 1 token 估算）
      4. 被采用的条 usage_count + 1，供下次排序参考
    """
    if not owner_key or not memory_enabled_for(owner_key):
        return ""

    db = SessionLocal()
    try:
        cards = db.execute(
            select(MemoryItem).where(
                MemoryItem.owner_key == owner_key,
                MemoryItem.kind == "card",
                MemoryItem.status == "active",
            )
        ).scalars().all()
        notes = db.execute(
            select(MemoryItem).where(
                MemoryItem.owner_key == owner_key,
                MemoryItem.kind == "note",
                MemoryItem.status == "active",
            )
        ).scalars().all()
        # key=_card_score 的意思是：key=lambda item: _card_score(item)
        cards = sorted(cards, key=_card_score, reverse=True)

        selected_cards: list[MemoryItem] = []

        per_category: dict[str, int] = {}
        for item in cards:
            # 按归一化后的类目分桶，避免同一类因写法不同被拆成多个桶
            category = normalize_category(item.category)
            # 限制每类最多 4 条：13 个分类下 8 条太宽，会挤掉其他类的名额
            if per_category.get(category, 0) >= 4:
                continue
            selected_cards.append(item)
            per_category[category] = per_category.get(category, 0) + 1
            # 达到上限后不再添加
            if len(selected_cards) >= settings.memory_cards_max:
                break

        notes = sorted(notes, key=lambda n: _note_score(n, query), reverse=True)
        selected_notes = [n for n in notes if _relevance(query, n.text) > 0][: settings.memory_notes_max]

        card_lines = []
        for item in selected_cards:
            # 注入前缀直接就是中文类目，历史上存的英文值也在这里被归一
            label = normalize_category(item.category)
            card_lines.append(f"- [{label}] {item.text}")
        note_lines = [f"- {item.text}" for item in selected_notes]

        if not card_lines and not note_lines:
            return ""

        parts = ["[用户长期记忆 · 仅供参考]"]
        if card_lines:
            parts.append("卡片：")
            parts.extend(card_lines)
        if note_lines:
            parts.append("相关背景：")
            parts.extend(note_lines)
        text = "\n".join(parts)

        # 粗略按 4 字符/token 截断：先丢 notes，再丢低分卡片
        budget_chars = max(200, settings.context_memory * 4)
        while len(text) > budget_chars and note_lines:
            note_lines.pop()
            parts = ["[用户长期记忆 · 仅供参考]"] + (["卡片："] + card_lines if card_lines else [])
            if note_lines:
                parts += ["相关背景："] + note_lines
            text = "\n".join(parts)
        while len(text) > budget_chars and card_lines:
            card_lines.pop()
            parts = ["[用户长期记忆 · 仅供参考]"] + (["卡片："] + card_lines if card_lines else [])
            if note_lines:
                parts += ["相关背景："] + note_lines
            text = "\n".join(parts)

        if not card_lines and not note_lines:
            return ""

        used_ids = [i.id for i in selected_cards] + [i.id for i in selected_notes]
        if used_ids:
            db.execute(
                update(MemoryItem)
                .where(MemoryItem.id.in_(used_ids))
                .values(usage_count=MemoryItem.usage_count + 1, last_used_at=now())
            )
            db.commit()
        return text
    finally:
        db.close()


def _serialize(item: MemoryItem) -> dict[str, Any]:
    """转成前端需要的字段；datetime 统一转 ISO 字符串（前端直接渲染）。"""
    return {
        "id": item.id,
        "kind": item.kind,
        "category": normalize_category(item.category),
        "key": item.key,
        "value": item.value,
        "text": item.text,
        "confidence": item.confidence,
        "mention_count": item.mention_count,
        "pinned": item.pinned,
        "source_run_id": item.source_run_id,
        "happened_at": item.happened_at.isoformat() if item.happened_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def get_memory_snapshot(conversation_id: str, owner_key: str, query: str) -> str:
    """读取会话级记忆快照；旧会话首次进入时懒生成一次。"""
    db = SessionLocal()
    try:
        conv = db.get(Conversation, conversation_id)
        if conv is None or conv.owner_key != owner_key:
            return ""
        if conv.memory_snapshot_at is not None:
            return conv.memory_snapshot or ""

        snapshot = load_memory_context(owner_key, query)
        # 条件更新：并发进入同一旧会话时只让一个请求写入
        result = db.execute(
            update(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.memory_snapshot_at.is_(None),
            )
            .values(memory_snapshot=snapshot, memory_snapshot_at=now())
        )
        db.commit()
        if result.rowcount:
            return snapshot
        db.expire(conv)
        return conv.memory_snapshot or ""
    finally:
        db.close()


def invalidate_memory_snapshots(owner_key: str) -> int:
    """用户编辑/删除/开关记忆后，让该 owner 的会话下次重新生成快照。"""
    db = SessionLocal()
    try:
        result = db.execute(
            update(Conversation)
            .where(Conversation.owner_key == owner_key)
            .values(memory_snapshot=None, memory_snapshot_at=None)
        )
        db.commit()
        return int(result.rowcount or 0)
    finally:
        db.close()


def list_memory(owner_key: str) -> dict[str, Any]:
    """列出当前身份的全部有效记忆，按卡片/笔记分组返回。"""
    db = SessionLocal()
    try:
        rows = db.execute(
            select(MemoryItem)
            .where(MemoryItem.owner_key == owner_key, MemoryItem.status == "active")
            .order_by(MemoryItem.kind, MemoryItem.updated_at.desc())
        ).scalars().all()
        cards = [_serialize(r) for r in rows if r.kind == "card"]
        notes = [_serialize(r) for r in rows if r.kind == "note"]
        setting = db.get(MemorySetting, owner_key)
        return {
            "enabled": setting.enabled if setting else True,
            "cards": cards,
            "notes": notes,
        }
    finally:
        db.close()


def update_memory_item(
    owner_key: str,
    item_id: str,
    *,
    text: str | None = None,
    value: Any = None,
    pinned: bool | None = None,
) -> dict[str, Any] | None:
    """用户手动编辑一条记忆；不属于自己的 id 直接当作不存在（返回 None）。

    text 按类型截断上限；改笔记文本要重算指纹，否则会撞唯一索引；
    改卡片 value 意味着旧结论被覆盖，mention_count 重置为 1。
    """
    db = SessionLocal()
    try:
        item = db.scalar(
            select(MemoryItem).where(
                MemoryItem.id == item_id,
                MemoryItem.owner_key == owner_key,
                MemoryItem.status == "active",
            )
        )
        if item is None:
            return None
        old = {"text": item.text, "value": item.value, "pinned": item.pinned}
        if text is not None:
            item.text = text[: settings.memory_note_chars if item.kind == "note" else settings.memory_card_chars]
            if item.kind == "note":
                item.fingerprint = _fingerprint(item.text)
        if value is not None and item.kind == "card":
            item.value = value
            item.mention_count = 1
        if pinned is not None:
            item.pinned = pinned
        item.updated_at = now()
        _record_event(
            db,
            owner_key,
            item.owner_kind,
            item.id,
            "update",
            old,
            {"text": item.text, "value": item.value, "pinned": item.pinned},
            None,
            actor="user",
        )
        db.commit()
        return _serialize(item)
    finally:
        db.close()


def delete_memory_item(owner_key: str, item_id: str) -> bool:
    """软删除单条记忆：只把 status 置为 deleted，保留行便于审计与回溯。"""
    db = SessionLocal()
    try:
        item = db.scalar(
            select(MemoryItem).where(
                MemoryItem.id == item_id,
                MemoryItem.owner_key == owner_key,
                MemoryItem.status == "active",
            )
        )
        if item is None:
            return False
        old = {"text": item.text, "value": item.value}
        item.status = "deleted"
        item.updated_at = now()
        _record_event(db, owner_key, item.owner_kind, item.id, "delete", old, None, None, actor="user")
        db.commit()
        return True
    finally:
        db.close()


def clear_memory(owner_key: str) -> int:
    """清空当前身份的全部记忆（软删除），返回影响条数。"""
    db = SessionLocal()
    try:
        count = db.execute(
            update(MemoryItem)
            .where(MemoryItem.owner_key == owner_key, MemoryItem.status == "active")
            .values(status="deleted", updated_at=now())
        ).rowcount or 0
        if count:
            _record_event(db, owner_key, _owner_kind(owner_key), None, "delete", None, {"count": count}, None, actor="user")
        db.commit()
        return int(count)
    finally:
        db.close()
