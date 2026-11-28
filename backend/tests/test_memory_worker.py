"""记忆提取 worker：任务队列抢单、模型返回结构兼容、schema 修复重试、证据校验后落库。"""

import threading
from uuid import uuid4

from sqlalchemy.exc import OperationalError

from app.config import settings
from app.db import SessionLocal
from app.models import MemoryJob, now
from app.services.memory import claim_memory_job, finish_memory_job, list_memory
from app.workers import document_index as index_worker
from app.workers import memory as worker
from app.workers import memory_extract
from tests.conftest import cleanup_owner


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
        cleanup_owner(owner)


def test_legacy_extraction_shape_is_normalized():
    # 复现线上 DeepSeek 返回的 id/type/content 形状
    result = worker.ExtractionResult.model_validate(
        {
            "cards": [
                {
                    "id": "user-name",
                    "type": "personal_info",
                    "content": "姓名：金显昱",
                    "source_message_id": "msg-1",
                }
            ],
            "notes": [
                {
                    "id": "onefold-platform",
                    "content": "用户在做 Onefold 平台。",
                    "source_message_id": "msg-2",
                }
            ],
        }
    )
    card = result.cards[0]
    # 未知类型（personal_info）不在 13 类中文枚举里，按设计降级为「其他」，不阻断提取
    assert (card.category, card.key, card.value) == (
        "其他",
        "user-name",
        "姓名：金显昱",
    )
    assert card.text == "姓名：金显昱"
    assert result.notes[0].text == "用户在做 Onefold 平台。"


def test_extract_repairs_invalid_schema_once(monkeypatch):
    # 第一次故意缺 source_message_id，第二次返回合法结构
    replies = iter(
        [
            '{"cards": [{"category": "profile", "key": "name", "value": "A", "text": "姓名：A"}], "notes": []}',
            '{"cards": [{"category": "profile", "key": "name", "value": "A", "text": "姓名：A", "source_message_id": "msg-1"}], "notes": []}',
        ]
    )
    calls = {"n": 0}

    def fake_call(*_args, **_kwargs):
        calls["n"] += 1
        return next(replies)

    monkeypatch.setattr(settings, "api_key", "test-key")
    # _call_model 定义在 memory_extract 里：patch 必须打在使用处，打门面无效
    monkeypatch.setattr(memory_extract, "_call_model", fake_call)
    result = worker._extract("user:test", [{"id": "msg-1", "role": "user", "content": "我叫 A"}], 0)
    assert calls["n"] == 2
    assert result.cards[0].source_message_id == "msg-1"


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
        cleanup_owner(owner)

def test_memory_loop_survives_db_failure(monkeypatch):
    """领取任务时的数据库异常（如 pg AdminShutdown）不能让 worker 线程退出。

    2026-11-28 线上事故：claim 在 try 之外，DB 重启把两个线程打死，
    进程因心跳线程仍在而被误判健康，任务永久停摆。此测试锁定该行为。
    """
    calls = {"n": 0}
    stop = threading.Event()

    def flaky_claim(worker_id: str):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OperationalError(
                "SELECT 1", {}, Exception("terminating connection due to administrator command")
            )
        stop.set()
        return None

    monkeypatch.setattr(worker, "claim_memory_job", flaky_claim)
    monkeypatch.setattr(worker, "RETRY_WAIT_S", 0.01, raising=False)

    thread = threading.Thread(target=worker.worker_loop, args=("test-loop", stop), daemon=True)
    thread.start()
    thread.join(timeout=3)

    assert not thread.is_alive(), "数据库异常后线程应继续运行而不是退出"
    assert calls["n"] >= 2, "第一次领取抛错后应退避重试，而不是结束循环"


def test_index_loop_survives_db_failure(monkeypatch):
    """索引 worker 的轮询循环同样必须容忍数据库异常。"""
    calls = {"n": 0}
    stop = threading.Event()

    def flaky_claim():
        calls["n"] += 1
        if calls["n"] == 1:
            raise OperationalError(
                "SELECT 1", {}, Exception("terminating connection due to administrator command")
            )
        stop.set()
        return None

    monkeypatch.setattr(index_worker, "cleanup_expired_documents", lambda: None)
    monkeypatch.setattr(index_worker, "claim_document_job", flaky_claim)
    monkeypatch.setattr(index_worker, "RETRY_WAIT_S", 0.01, raising=False)

    thread = threading.Thread(target=index_worker.worker_loop, args=("test-loop", stop), daemon=True)
    thread.start()
    thread.join(timeout=3)

    assert not thread.is_alive(), "数据库异常后线程应继续运行而不是退出"
    assert calls["n"] >= 2, "第一次领取抛错后应退避重试，而不是结束循环"
