"""知识库作用域与权限：public 可读，personal 按 owner 隔离。"""

from uuid import uuid4

from sqlalchemy import and_, false, or_, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import KnowledgeBase, now

PUBLIC_KB_ID = "public"
PUBLIC_OWNER_KEY = "public"


def is_admin(principal) -> bool:
    return principal.role in ("admin", "superadmin")


def get_kb(db: Session, kb_id: str | None) -> KnowledgeBase | None:
    return db.get(KnowledgeBase, kb_id) if kb_id else None


def ensure_public_kb(db: Session) -> KnowledgeBase:
    kb = db.get(KnowledgeBase, PUBLIC_KB_ID)
    if kb is None:
        kb = KnowledgeBase(
            id=PUBLIC_KB_ID,
            kind="public",
            name="公共知识库",
            owner_key=None,
            status="active",
            created_at=now(),
            updated_at=now(),
        )
        db.add(kb)
        db.flush()
    return kb


def get_or_create_personal_kb(db: Session, owner_key: str) -> KnowledgeBase:
    kb = db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.kind == "personal",
            KnowledgeBase.owner_key == owner_key,
        )
    ).scalar_one_or_none()
    if kb is None:
        kb = KnowledgeBase(
            id=str(uuid4()),
            kind="personal",
            name="个人知识库",
            owner_key=owner_key,
            status="active",
            created_at=now(),
            updated_at=now(),
        )
        db.add(kb)
        db.flush()
    return kb


def visible_kb_condition(owner_key: str, allow_public: bool):
    """检索用 SQL 条件；owner 为空时只允许公共库（如果有）。"""
    parts = []
    if allow_public:
        parts.append(KnowledgeBase.kind == "public")
    if owner_key:
        parts.append(
            and_(
                KnowledgeBase.kind == "personal",
                KnowledgeBase.owner_key == owner_key,
            )
        )
    return and_(
        KnowledgeBase.status == "active",
        or_(*parts) if parts else false(),
    )


def public_read_allowed(principal) -> bool:
    if principal.kind == "user":
        return True
    return settings.public_kb_guest_read


def can_write_kb(principal, kb: KnowledgeBase | None) -> bool:
    if kb is None:
        return False
    if kb.kind == "public":
        return is_admin(principal)
    return kb.kind == "personal" and kb.owner_key == principal.owner_key


def scope_label(kb: KnowledgeBase | None, kind: str) -> str:
    if kb is not None and kb.kind == "public":
        return "公共知识库"
    if kind == "temp":
        return "临时文档"
    return "个人知识库"
