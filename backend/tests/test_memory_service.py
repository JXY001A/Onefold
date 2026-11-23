"""记忆服务层：写入/强化/编辑、开关、会话快照、分类归一。"""

from uuid import uuid4

from sqlalchemy import delete

from app.db import SessionLocal
from app.models import Conversation
from app.services.history import get_or_create_conversation
from app.services.memory import (
    CATEGORIES,
    apply_extraction,
    clear_memory,
    delete_memory_item,
    get_memory_snapshot,
    invalidate_memory_snapshots,
    list_memory,
    load_memory_context,
    normalize_category,
    set_memory_enabled,
    update_memory_item,
)
from tests.conftest import cleanup_owner


def test_memory_service_cards_notes_and_reinforcement():
    owner = f"user:{uuid4()}"
    try:
        stats = apply_extraction(
            owner,
            "run-1",
            [
                {
                    "category": "preference",
                    "key": "answer_style",
                    "value": "先给结论",
                    "text": "偏好：回答先给结论",
                    "confidence": 0.9,
                }
            ],
            [
                {
                    "category": "project",
                    "text": "用户把 Onefold 从 SQLite 换成了 PostgreSQL。",
                    "confidence": 0.85,
                }
            ],
        )
        assert stats["added"] == 1
        assert stats["notes"] == 1

        data = list_memory(owner)
        assert len(data["cards"]) == 1
        assert len(data["notes"]) == 1

        # 同一卡片再次出现：只强化，不新增
        stats = apply_extraction(
            owner,
            "run-2",
            [
                {
                    "category": "preference",
                    "key": "answer_style",
                    "value": "先给结论",
                    "text": "偏好：回答先给结论",
                    "confidence": 0.9,
                }
            ],
            [],
        )
        assert stats["reinforced"] == 1
        assert list_memory(owner)["cards"][0]["mention_count"] == 2

        # 卡片值变化：更新而不是继续强化
        stats = apply_extraction(
            owner,
            "run-3",
            [
                {
                    "category": "preference",
                    "key": "answer_style",
                    "value": "先给结论，再展开",
                    "text": "偏好：先给结论，再展开",
                    "confidence": 0.9,
                }
            ],
            [],
        )
        assert stats["updated"] == 1
        card = list_memory(owner)["cards"][0]
        assert card["value"] == "先给结论，再展开"
        assert card["mention_count"] == 1

        text = load_memory_context(owner, "回答风格")
        assert "用户长期记忆" in text
        assert "先给结论" in text

        # 编辑与删除
        assert update_memory_item(owner, card["id"], text="偏好：先结论")
        assert list_memory(owner)["cards"][0]["text"] == "偏好：先结论"
        assert delete_memory_item(owner, card["id"])
        assert all(c["id"] != card["id"] for c in list_memory(owner)["cards"])

        assert clear_memory(owner) >= 1
        assert list_memory(owner)["cards"] == []
        assert list_memory(owner)["notes"] == []
    finally:
        cleanup_owner(owner)


def test_memory_setting_can_disable_injection():
    owner = f"user:{uuid4()}"
    try:
        apply_extraction(
            owner,
            "run-disable",
            [{"category": "profile", "key": "role", "value": "前端", "text": "职业：前端", "confidence": 1}],
            [],
        )
        assert load_memory_context(owner, "职业")
        set_memory_enabled(owner, False)
        assert load_memory_context(owner, "职业") == ""
    finally:
        cleanup_owner(owner)


def test_memory_snapshot_is_frozen_until_invalidated():
    owner = f"user:{uuid4()}"
    try:
        conversation_id = get_or_create_conversation(owner, title_seed="测试会话")
        apply_extraction(
            owner,
            "run-snap-1",
            [{"category": "preference", "key": "style", "value": "先结论", "text": "偏好：先结论", "confidence": 0.9}],
            [],
        )
        first = get_memory_snapshot(conversation_id, owner, "回答风格")
        assert "先结论" in first

        # worker 更新记忆不改变已冻结的会话快照
        apply_extraction(
            owner,
            "run-snap-2",
            [{"category": "preference", "key": "style", "value": "先结论再展开", "text": "偏好：先结论再展开", "confidence": 0.9}],
            [],
        )
        assert get_memory_snapshot(conversation_id, owner, "回答风格") == first

        # 用户主动失效后，下一轮重建
        assert invalidate_memory_snapshots(owner) >= 1
        second = get_memory_snapshot(conversation_id, owner, "回答风格")
        assert "先结论再展开" in second
    finally:
        with SessionLocal() as db:
            db.execute(delete(Conversation).where(Conversation.owner_key == owner))
            db.commit()
        cleanup_owner(owner)


def test_normalize_category_maps_aliases_and_falls_back():
    # 中文枚举值原样保留（含两端空白）
    for name in CATEGORIES:
        assert normalize_category(name) == name
        assert normalize_category(f"  {name} ") == name
    # 历史英文值与常见别名统一归到对应中文类目
    assert normalize_category("profile") == "身份"
    assert normalize_category("Preference") == "偏好"
    assert normalize_category("career") == "职业"
    assert normalize_category("skills") == "技能"
    assert normalize_category("hobby") == "兴趣"
    # 认不出的值一律落到「其他」，不允许脏值进库
    assert normalize_category("personal_info") == "其他"
    assert normalize_category(None) == "其他"
    assert normalize_category("") == "其他"