"""记忆写入：把 worker 校验后的结果落库，并记录变更审计。

card 以 (category, key) 判重，note 以文本指纹（归一化后的 sha256）判重。
"""

import hashlib
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from ..db import SessionLocal
from ..models import MemoryEvent, MemoryItem, now
from .memory_categories import normalize_category
from .memory_scope import owner_kind


def text_fingerprint(text: str) -> str:
    """笔记去重指纹：归一化后取 sha256，同一句话换种写法也能判重。

    只用于 note（没有 key 的自由文本）；card 靠 category + key 判重。
    """
    normalized = " ".join(str(text or "").lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def record_event(
    db,
    owner_key: str,
    kind: str,
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
            owner_kind=kind,
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
    kind = owner_kind(owner_key)
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
                    owner_kind=kind,
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
                record_event(db, owner_key, kind, row.id, "add", None, {"value": value, "text": row.text}, run_id)
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
                record_event(db, owner_key, kind, existing.id, "update", old, {"value": value, "text": existing.text}, run_id)
                stats["updated"] += 1

        for note in notes:
            # 唯一键：文本指纹：可以理解为针对这段文本生成了唯一一个指纹，文本不变则指纹相同
            text_value = str(note["text"])
            fp = text_fingerprint(text_value)
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
                owner_kind=kind,
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
            record_event(db, owner_key, kind, row.id, "add", None, {"text": text_value}, run_id)
            stats["notes"] += 1

        db.commit()
        return stats
    finally:
        db.close()


def serialize_item(item: MemoryItem) -> dict[str, Any]:
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