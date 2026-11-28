"""访客身份：发放 guest_id，以及在注册时把访客数据一次性归到账号名下。

边界：只有注册会「收养」访客数据；登录一律不迁移，避免同一浏览器上
多个账号互相串数据（公用电脑场景）。注册完成后旧 guest_id 立即作废，
后续再以访客身份访问会拿到全新 id，不会与任何账号历史交叉。
"""

from datetime import datetime, timedelta, timezone

import secrets

from fastapi import Request, Response
from sqlalchemy.orm import Session

from ..config import settings
from ..roles import OwnerKind, owner_key_for
from ..models import (
    Conversation,
    ConversationSummary,
    DocumentJob,
    GuestSession,
    MemoryEvent,
    MemoryItem,
    MemoryJob,
    MemorySetting,
    Visit,
)

# 30 天滑动有效期：每次进入站点（/api/auth/guest）都顺延过期时间，
# 所以「连续 30 天没来」才会失去身份，而不是从首次访问起算 30 天。
GUEST_TTL_HOURS = 24 * 30


def _as_utc(value: datetime) -> datetime:
    """SQLite 取回的 datetime 没有时区，统一补成 UTC 再比较。"""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def issue_guest(db: Session, request: Request, response: Response) -> int:
    """确保浏览器持有未过期的访客身份，返回 Cookie 有效期（秒）。

    复用未过期 Cookie，避免每次刷新都新建访客记录；过期则换一个新 id。
    """
    now = datetime.now(timezone.utc)
    guest_id = request.cookies.get("guest_id")
    row = db.get(GuestSession, guest_id) if guest_id else None
    expires_at = now + timedelta(hours=GUEST_TTL_HOURS)

    if row is None or _as_utc(row.expires_at) <= now:
        guest_id = secrets.token_urlsafe(24)
        row = GuestSession(
            id=guest_id,
            ip=request.client.host if request.client else None,
            user_agent=(request.headers.get("user-agent") or "")[:255] or None,
            created_at=now,
            last_seen_at=now,
            expires_at=expires_at,
        )
        db.add(row)
    else:
        # 滑动续期：老访客每来一次就把有效期往后推 30 天
        row.last_seen_at = now
        row.expires_at = expires_at

    db.commit()

    # HttpOnly 防 XSS 读取；Secure 由部署环境控制，线上 HTTPS 必须为 True
    response.set_cookie(
        "guest_id",
        guest_id,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=GUEST_TTL_HOURS * 3600,
        path="/",
    )
    return GUEST_TTL_HOURS * 3600


def adopt_guest(db: Session, guest_id: str, user_id: str) -> dict[str, int]:
    """把 guest:<id> 名下的会话、访问与记忆整体改挂到 user:<id>。

    只在注册时调用：此时 user 刚建好、名下没有任何数据，因此不会违反
    memory_items 的 (owner_key, key) 活跃唯一索引，也不会与开关表主键冲突。
    runs.user_id 不在此处理：访客的 Run 本来存的就是 None，无需改写。
    """
    old, new = owner_key_for(OwnerKind.GUEST, guest_id), owner_key_for(OwnerKind.USER, user_id)
    return {
        "conversations": _reassign(db, Conversation, old, new),
        # 访问记录同时改 kind，画像才能跨身份算在登录用户名下
        "visits": db.query(Visit)
        .filter(Visit.owner_key == old)
        .update({Visit.owner_key: new, Visit.kind: OwnerKind.USER}, synchronize_session=False),
        "memory_items": _reassign(db, MemoryItem, old, new),
        "memory_jobs": _reassign(db, MemoryJob, old, new),
        "memory_events": _reassign(db, MemoryEvent, old, new),
        "summaries": _reassign(db, ConversationSummary, old, new),
        "document_jobs": _reassign(db, DocumentJob, old, new),
        "memory_settings": _move_setting(db, old, new),
    }


def _reassign(db: Session, model, old: str, new: str) -> int:
    """按 owner_key 批量改归属，返回影响行数。"""
    return (
        db.query(model)
        .filter(model.owner_key == old)
        .update({model.owner_key: new}, synchronize_session=False)
    )


def _move_setting(db: Session, old: str, new: str) -> int:
    """开关表以 owner_key 作主键，不能直接 UPDATE，只能删旧插新。"""
    row = db.get(MemorySetting, old)
    if row is None:
        return 0
    enabled, updated_at = row.enabled, row.updated_at
    db.delete(row)
    db.flush()  # 先落删除，避免插新行时主键冲突
    if db.get(MemorySetting, new) is None:
        db.add(MemorySetting(owner_key=new, enabled=enabled, updated_at=updated_at))
    return 1


def rotate_guest_cookie(response: Response) -> None:
    """注册成功后清掉 guest_id：之后以访客身份访问会拿到全新 id。"""
    response.delete_cookie("guest_id", path="/")