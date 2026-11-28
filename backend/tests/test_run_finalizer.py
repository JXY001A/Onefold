"""run_finalizer：记忆任务的登记条件。

2026-11-28 修复：原判断写死 role == "user"，而账号角色实际是
member / admin / superadmin / guest，导致只有访客能登记记忆任务。
本测试锁定：所有登录角色都登记；访客仍按最低轮次门槛。
"""

from app.services import run_finalizer


def _enqueued(monkeypatch, *, role: str, rounds: int = 0) -> int:
    """在全部依赖被隔离的前提下调用 finalize_run，返回入队次数。"""
    calls = {"n": 0}

    monkeypatch.setattr(run_finalizer, "save_transcript", lambda *a, **k: None)
    monkeypatch.setattr(run_finalizer, "finish_run", lambda *a, **k: None)
    monkeypatch.setattr(run_finalizer, "schedule_compaction", lambda *a, **k: None)
    monkeypatch.setattr(run_finalizer, "memory_enabled_for", lambda owner: True)
    monkeypatch.setattr(run_finalizer, "rounds_used", lambda owner: rounds)
    monkeypatch.setattr(
        run_finalizer, "enqueue_memory_job", lambda **k: calls.__setitem__("n", calls["n"] + 1)
    )

    run_finalizer.finalize_run(
        run_id="run-1",
        status="done",
        owner_key="guest:abc" if role == "guest" else "user:abc",
        user_id=None,
        role=role,
        conversation_id="conv-1",
        message="你好",
        transcript=[{"role": "user", "content": "你好"}],
    )
    return calls["n"]


def test_all_logged_in_roles_enqueue_memory_job(monkeypatch):
    for role in ("member", "admin", "superadmin"):
        assert _enqueued(monkeypatch, role=role) == 1, f"角色 {role} 必须登记记忆任务"


def test_guest_enqueues_only_after_min_rounds(monkeypatch):
    assert _enqueued(monkeypatch, role="guest", rounds=0) == 0
    assert _enqueued(monkeypatch, role="guest", rounds=99) == 1
