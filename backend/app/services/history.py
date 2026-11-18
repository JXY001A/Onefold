"""会话存取：会话元信息（conversations）、历史消息（messages）与每轮执行（runs）。

数据层级：
    conversations（会话：标题 / 归属 / 活跃时间）
        └── runs（每轮执行：状态 / 耗时 / token）
                └── messages（消息：角色 / 内容）

归属统一用 owner_key（格式与 Principal.lock_key 一致）：
    user:<user_id>    登录用户
    guest:<guest_id>  匿名访客
两种身份走同一套规则，访客因此也能拥有多个会话。

注意：messages 表只有 run_id，所以「按会话查消息」必须借道 runs：
    messages.run_id → runs.id，再由 runs.conversation_id 过滤。
"""

from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select

from ..db import SessionLocal
from ..models import Conversation, Message, Run, now

# 标题取首条用户消息的前 N 个字
TITLE_MAX = 30


def _make_title(text: str | None) -> str | None:
    """把首条消息压成一行标题（压缩空白 + 超长截断）。"""
    if not text:
        return None
    title = " ".join(text.split())
    if not title:
        return None
    return title[:TITLE_MAX] + ("…" if len(title) > TITLE_MAX else "")


def get_or_create_conversation(
    owner_key: str,
    conversation_id: str | None = None,
    title_seed: str | None = None,
) -> str:
    """定位或新建会话，并刷新活跃时间（列表按它排序），返回 conversation_id。

    - 传入 conversation_id：必须存在且属于 owner_key，否则抛 PermissionError；
    - 不传：新建会话，标题取首条用户消息。
    """
    db = SessionLocal()
    try:
        if conversation_id:
            conv = db.get(Conversation, conversation_id)
            if conv is None or conv.owner_key != owner_key:
                raise PermissionError(conversation_id)
            conv.updated_at = now()
            # 早期建的空标题会话，等首条消息补上
            if not conv.title:
                conv.title = _make_title(title_seed)
            db.commit()
            return conv.id

        conv = Conversation(
            id=str(uuid4()),
            owner_key=owner_key,
            title=_make_title(title_seed),
            created_at=now(),
            updated_at=now(),
        )
        db.add(conv)
        db.commit()
        return conv.id
    finally:
        db.close()


def conversation_owned_by(conversation_id: str, owner_key: str) -> bool:
    """会话是否属于该身份。登录用户与访客统一按 owner_key 判断。"""
    db = SessionLocal()
    try:
        conv = db.get(Conversation, conversation_id)
        return conv is not None and conv.owner_key == owner_key
    finally:
        db.close()


def list_conversations(owner_key: str, days: int = 20, limit: int = 100) -> list[dict]:
    """最近 days 天内有过活动的会话，按活跃时间倒序。"""
    since = now() - timedelta(days=days)
    db = SessionLocal()
    try:
        stmt = (
            select(Conversation)
            .where(
                Conversation.owner_key == owner_key,
                Conversation.updated_at >= since,
            )
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        rows = db.execute(stmt).scalars()
        return [
            {
                "conversation_id": c.id,
                "title": c.title or "新对话",
                "updated_at": c.updated_at.isoformat(),
            }
            for c in db.execute(stmt).scalars()
        ]
    finally:
        db.close()


def load_conversation_messages(conversation_id: str, limit: int = 200) -> list[dict]:
    """按会话读取消息（带时间，供前端渲染历史），取最近 limit 条后转正序。

    归属校验由调用方先做（本函数只负责取数）。
    """
    db = SessionLocal()
    try:
        stmt = (
            select(Message.role, Message.content, Message.created_at)
            .join(Run, Message.run_id == Run.id)
            .where(
                Run.conversation_id == conversation_id,
                Message.role.in_(("user", "assistant")),
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        rows = db.execute(stmt).all()
        return [
            {
                "role": r.role,
                "content": r.content,
                "created_at": r.created_at.isoformat(),
            }
            for r in reversed(rows)
        ]
    finally:
        db.close()


def load_history(
    owner_key: str,
    conversation_id: str | None,
    limit: int = 100,
) -> list[dict]:
    """给 LLM 的对话上下文，返回 [{"role": ..., "content": ...}]。

    查询时 JOIN conversations 顺带校验归属（双保险：调用方已校验过一次）；
    limit 只取最近 N 条，真正的 token 裁剪由 build_messages 按 context_history 再做。
    """
    if not owner_key or not conversation_id:
        return []

    db = SessionLocal()
    try:
        stmt = (
            select(Message.role, Message.content)
            .join(Run, Message.run_id == Run.id)
            .join(Conversation, Conversation.id == Run.conversation_id)
            .where(
                Run.conversation_id == conversation_id,
                Conversation.owner_key == owner_key,
                Message.role.in_(("user", "assistant")),
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        rows = db.execute(stmt).all()
        # 先倒序取最近 N 条，再反转回正序（从旧到新）
        return [{"role": r.role, "content": r.content} for r in reversed(rows)]
    finally:
        db.close()


def save_message(run_id: str, role: str, content: str) -> None:
    """把一条消息写入数据库，归属到指定的 run（会话归属由该 run 的 conversation_id 决定）。"""
    db = SessionLocal()
    try:
        db.add(Message(id=str(uuid4()), run_id=run_id, role=role, content=content))
        db.commit()
    finally:
        db.close()


def create_run(user_id: str | None, conversation_id: str | None) -> str:
    """开始一轮对话：先建 run 记录，后续消息都挂在这个 run 下。返回 run_id。"""
    run_id = str(uuid4())
    db = SessionLocal()
    try:
        db.add(
            Run(
                id=run_id,
                user_id=user_id,
                conversation_id=conversation_id,
                status="running",
                started_at=now(),
            )
        )
        db.commit()
    finally:
        db.close()
    return run_id


def finish_run(run_id: str, status: str = "done", error: str | None = None) -> None:
    """结束一轮对话：更新 run 状态与结束时间。status: done / cancelled / error。"""
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        if run:
            run.status = status
            run.ended_at = now()
            run.error = error
            db.commit()
    finally:
        db.close()