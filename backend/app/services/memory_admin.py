"""用户侧记忆管理：列表、编辑、软删除、清空。

全部是写操作，调用方负责在完成后让会话记忆快照失效。
"""

from typing import Any

from sqlalchemy import select, update

from ..config import settings
from ..db import SessionLocal
from ..models import MemoryItem, MemorySetting, now
from .memory_scope import owner_kind
from .memory_store import record_event, serialize_item, text_fingerprint


def list_memory(owner_key: str) -> dict[str, Any]:
    """列出当前身份的全部有效记忆，按卡片/笔记分组返回。"""
    db = SessionLocal()
    try:
        rows = db.execute(
            select(MemoryItem)
            .where(MemoryItem.owner_key == owner_key, MemoryItem.status == "active")
            .order_by(MemoryItem.kind, MemoryItem.updated_at.desc())
        ).scalars().all()
        cards = [serialize_item(r) for r in rows if r.kind == "card"]
        notes = [serialize_item(r) for r in rows if r.kind == "note"]
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
                item.fingerprint = text_fingerprint(item.text)
        if value is not None and item.kind == "card":
            item.value = value
            item.mention_count = 1
        if pinned is not None:
            item.pinned = pinned
        item.updated_at = now()
        record_event(
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
        return serialize_item(item)
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
        record_event(db, owner_key, item.owner_kind, item.id, "delete", old, None, None, actor="user")
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
            record_event(db, owner_key, owner_kind(owner_key), None, "delete", None, {"count": count}, None, actor="user")
        db.commit()
        return int(count)
    finally:
        db.close()