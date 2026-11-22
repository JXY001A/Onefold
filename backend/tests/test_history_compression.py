"""历史摘要压缩的回归测试。"""

from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.config import settings
from app.db import SessionLocal
from app.models import Conversation, ConversationSummary, Message, Run, now
from app.services.history import estimate_tokens, load_history, maybe_compact_history


def _create_conversation(owner_key: str) -> str:
    conversation_id = str(uuid4())
    with SessionLocal() as db:
        db.add(
            Conversation(
                id=conversation_id,
                owner_key=owner_key,
                created_at=now(),
                updated_at=now(),
            )
        )
        db.commit()
    return conversation_id


def _add_run(conversation_id: str, turn_no: int, user_text: str, assistant_text: str) -> str:
    run_id = str(uuid4())
    created_at = now()
    with SessionLocal() as db:
        db.add(
            Run(
                id=run_id,
                conversation_id=conversation_id,
                turn_no=turn_no,
                status="done",
                started_at=created_at,
                ended_at=created_at,
            )
        )
        db.add(
            Message(
                id=str(uuid4()),
                run_id=run_id,
                role="user",
                content=user_text,
                seq=1,
                created_at=created_at,
            )
        )
        db.add(
            Message(
                id=str(uuid4()),
                run_id=run_id,
                role="assistant",
                content=assistant_text,
                seq=2,
                created_at=created_at,
            )
        )
        db.commit()
    return run_id


def _cleanup(conversation_id: str) -> None:
    with SessionLocal() as db:
        run_ids = list(
            db.execute(select(Run.id).where(Run.conversation_id == conversation_id)).scalars()
        )
        if run_ids:
            db.execute(delete(Message).where(Message.run_id.in_(run_ids)))
        db.execute(
            delete(ConversationSummary).where(
                ConversationSummary.conversation_id == conversation_id
            )
        )
        db.execute(delete(Run).where(Run.conversation_id == conversation_id))
        db.execute(delete(Conversation).where(Conversation.id == conversation_id))
        db.commit()


def test_estimate_tokens_handles_chinese_and_ascii():
    assert estimate_tokens("") == 0
    assert estimate_tokens("你好") >= 2
    assert estimate_tokens("hello world") >= 2


@pytest.mark.asyncio
async def test_compact_history_keeps_recent_raw_runs(monkeypatch):
    owner_key = f"user:{uuid4()}"
    conversation_id = _create_conversation(owner_key)
    monkeypatch.setattr(settings, "history_compact_tokens", 5)

    try:
        for turn_no in range(1, 7):
            _add_run(conversation_id, turn_no, f"用户问题{turn_no}", f"回答{turn_no}")

        async def fake_summarizer(source: str) -> str:
            assert "用户问题1" in source
            assert "用户问题2" in source
            return "第 1-2 轮摘要"

        assert await maybe_compact_history(
            conversation_id, owner_key, summarizer=fake_summarizer
        )

        with SessionLocal() as db:
            conv = db.get(Conversation, conversation_id)
            assert conv is not None
            assert conv.summarized_until_turn_no == 2
            summaries = list(
                db.execute(
                    select(ConversationSummary).where(
                        ConversationSummary.conversation_id == conversation_id
                    )
                ).scalars()
            )
            assert len(summaries) == 1
            assert summaries[0].from_turn_no == 1
            assert summaries[0].to_turn_no == 2
            assert summaries[0].summary == "第 1-2 轮摘要"

        history = load_history(owner_key, conversation_id)
        assert history[0]["role"] == "system"
        assert "第 1-2 轮摘要" in history[0]["content"]

        joined = "\n".join(m.get("content") or "" for m in history)
        assert "用户问题1" not in joined
        assert "用户问题2" not in joined
        for turn_no in range(3, 7):
            assert f"用户问题{turn_no}" in joined

        # 再次执行不会重复压缩：最近 4 轮仍然保留，指针已经到 2。
        assert not await maybe_compact_history(
            conversation_id, owner_key, summarizer=fake_summarizer
        )
    finally:
        _cleanup(conversation_id)


@pytest.mark.asyncio
async def test_compaction_failure_keeps_pointer_and_raw_history(monkeypatch):
    owner_key = f"user:{uuid4()}"
    conversation_id = _create_conversation(owner_key)
    monkeypatch.setattr(settings, "history_compact_tokens", 5)

    try:
        for turn_no in range(1, 7):
            _add_run(conversation_id, turn_no, f"用户问题{turn_no}", f"回答{turn_no}")

        async def failing_summarizer(_source: str) -> str:
            raise RuntimeError("summary api failed")

        assert not await maybe_compact_history(
            conversation_id, owner_key, summarizer=failing_summarizer
        )

        with SessionLocal() as db:
            conv = db.get(Conversation, conversation_id)
            assert conv is not None
            assert conv.summarized_until_turn_no == 0
            assert (
                db.execute(
                    select(ConversationSummary).where(
                        ConversationSummary.conversation_id == conversation_id
                    )
                ).first()
                is None
            )

        history = load_history(owner_key, conversation_id)
        joined = "\n".join(m.get("content") or "" for m in history)
        assert "用户问题1" in joined
    finally:
        _cleanup(conversation_id)


@pytest.mark.asyncio
async def test_compaction_skips_below_threshold(monkeypatch):
    owner_key = f"user:{uuid4()}"
    conversation_id = _create_conversation(owner_key)
    monkeypatch.setattr(settings, "history_compact_tokens", 100_000)

    called = False

    async def fake_summarizer(_source: str) -> str:
        nonlocal called
        called = True
        return "不应该被调用"

    try:
        for turn_no in range(1, 7):
            _add_run(conversation_id, turn_no, f"用户问题{turn_no}", f"回答{turn_no}")

        assert not await maybe_compact_history(
            conversation_id, owner_key, summarizer=fake_summarizer
        )
        assert not called

        with SessionLocal() as db:
            conv = db.get(Conversation, conversation_id)
            assert conv is not None
            assert conv.summarized_until_turn_no == 0
    finally:
        _cleanup(conversation_id)
