"""长期记忆服务与 API 的回归测试。"""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models import MemoryEvent, MemoryItem, MemoryJob, MemorySetting, now
from app.services.memory import (
    apply_extraction,
    claim_memory_job,
    clear_memory,
    delete_memory_item,
    finish_memory_job,
    list_memory,
    load_memory_context,
    set_memory_enabled,
    update_memory_item,
)
from app.workers import memory as worker


def _cleanup(owner_key: str) -> None:
    with SessionLocal() as db:
        db.execute(delete(MemoryEvent).where(MemoryEvent.owner_key == owner_key))
        db.execute(delete(MemoryItem).where(MemoryItem.owner_key == owner_key))
        db.execute(delete(MemoryJob).where(MemoryJob.owner_key == owner_key))
        db.execute(delete(MemorySetting).where(MemorySetting.owner_key == owner_key))
        db.commit()


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
        _cleanup(owner)


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
        _cleanup(owner)


def test_claim_and_finish_job():
    owner = f"user:{uuid4()}"
    job_id = str(uuid4())
    try:
        with SessionLocal() as db:
            db.add(
                MemoryJob(
                    id=job_id,
                    owner_key=owner,
                    owner_kind="user",
                    run_id=job_id,
                    status="pending",
                    priority=0,
                    run_after=now(),
                    created_at=now(),
                )
            )
            db.commit()

        job = claim_memory_job("test-worker")
        assert job is not None
        assert job["id"] == job_id
        assert job["attempts"] == 1

        finish_memory_job(job_id, "empty", {"cards": 0, "notes": 0})
        with SessionLocal() as db:
            row = db.get(MemoryJob, job_id)
            assert row.status == "done"
            assert row.result == "empty"
    finally:
        _cleanup(owner)


def test_worker_process_job_with_mocked_llm(monkeypatch):
    owner = f"user:{uuid4()}"
    try:
        # 不调真实 DeepSeek，只验证“证据校验 -> 落库”链路
        monkeypatch.setattr(
            worker,
            "run_turns",
            lambda *_args, **_kwargs: [
                {"id": "msg-1", "run_id": "run-x", "role": "user", "content": "以后回答先给结论"},
                {"id": "msg-2", "run_id": "run-x", "role": "assistant", "content": "好的"},
            ],
        )
        monkeypatch.setattr(
            worker,
            "_extract",
            lambda *_args, **_kwargs: worker.ExtractionResult(
                cards=[
                    worker.CardOp(
                        category="preference",
                        key="answer_style",
                        value="先给结论",
                        text="偏好：先给结论",
                        confidence=0.9,
                        source_message_id="msg-1",
                    )
                ],
                notes=[],
            ),
        )
        worker.process_job(
            {
                "id": str(uuid4()),
                "owner_key": owner,
                "owner_kind": "user",
                "run_id": str(uuid4()),
                "conversation_id": str(uuid4()),
                "attempts": 1,
                "priority": 0,
            }
        )
        cards = list_memory(owner)["cards"]
        assert len(cards) == 1
        assert cards[0]["text"] == "偏好：先给结论"
    finally:
        _cleanup(owner)


def test_guest_memory_api_crud():
    with TestClient(app) as client:
        assert client.post("/api/auth/guest").status_code == 200
        guest_id = client.cookies["guest_id"]
        owner = f"guest:{guest_id}"
        try:
            apply_extraction(
                owner,
                "run-api",
                [{"category": "preference", "key": "units", "value": "公制", "text": "偏好：公制单位", "confidence": 0.9}],
                [],
            )
            data = client.get("/api/memory").json()
            assert data["enabled"] is True
            assert len(data["cards"]) == 1
            item_id = data["cards"][0]["id"]

            assert client.patch("/api/memory/settings", json={"enabled": False}).status_code == 200
            assert client.get("/api/memory").json()["enabled"] is False
            assert client.patch("/api/memory/settings", json={"enabled": True}).status_code == 200

            res = client.patch(f"/api/memory/{item_id}", json={"text": "偏好：统一用公制"})
            assert res.status_code == 200
            assert res.json()["text"] == "偏好：统一用公制"

            assert client.delete(f"/api/memory/{item_id}").status_code == 200
            assert client.get("/api/memory").json()["cards"] == []
        finally:
            _cleanup(owner)
