"""记忆注入：挑选条目、渲染成提示词、维护会话级快照。

分数由 memory_scoring 提供；这里只负责按预算裁剪与文本拼接。
超预算时先丢笔记，再丢低分卡片。
"""

from sqlalchemy import select, update

from ..config import settings
from ..db import SessionLocal
from ..models import Conversation, MemoryItem, now
from .memory_categories import normalize_category
from .memory_scope import memory_enabled_for
from .memory_scoring import card_score, note_score, relevance


def load_memory_context(owner_key: str, query: str) -> str:
    """读取并渲染注入文本；没有记忆/关闭时返回空串。

    筛选顺序：
      1. 卡片按 card_score 排序，同类目最多 4 条、总数受 memory_cards_max 限制
      2. 笔记只保留与当前问题相关的（relevance > 0），取前 memory_notes_max 条
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
        # key=card_score 的意思是：key=lambda item: card_score(item)
        cards = sorted(cards, key=card_score, reverse=True)

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

        notes = sorted(notes, key=lambda n: note_score(n, query), reverse=True)
        selected_notes = [n for n in notes if relevance(query, n.text) > 0][: settings.memory_notes_max]

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