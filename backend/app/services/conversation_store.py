"""会话元信息：定位/新建会话、归属校验、会话列表。

消息与轮次的读写不在这里，见 message_reader / run_store。
"""

from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select

from ..db import SessionLocal
from ..models import Conversation, now

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