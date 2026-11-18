"""访客身份隔离的回归测试：独立 Cookie、独立会话、跨访客拒绝。"""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import GuestSession


def test_guest_session_and_chat():
    with TestClient(app) as client:
        assert client.get("/api/auth/me").status_code == 401

        assert client.post("/api/auth/guest").status_code == 200
        assert client.cookies.get("guest_id")

        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json() == {"kind": "guest"}

        chat = client.post("/api/chat", json={"message": "你好"})
        assert chat.status_code == 200
        assert chat.headers["content-type"].startswith("text/event-stream")
        assert "event: done" in chat.text


def test_two_guests_get_distinct_ids():
    with TestClient(app) as a, TestClient(app) as b:
        assert a.post("/api/auth/guest").status_code == 200
        assert b.post("/api/auth/guest").status_code == 200
        assert a.cookies["guest_id"] != b.cookies["guest_id"]


def test_chat_requires_identity():
    with TestClient(app) as client:
        assert client.post("/api/chat", json={"message": "hi"}).status_code == 401


def test_guest_cannot_use_another_conversation():
    with TestClient(app) as client:
        assert client.post("/api/auth/guest").status_code == 200
        res = client.post(
            "/api/chat",
            json={"message": "hi", "conversation_id": "someone-else"},
        )
        assert res.status_code == 403


def test_expired_guest_is_rejected_and_replaced():
    with TestClient(app) as client:
        assert client.post("/api/auth/guest").status_code == 200
        old_id = client.cookies["guest_id"]

        with SessionLocal() as db:
            row = db.get(GuestSession, old_id)
            row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()

        assert client.get("/api/auth/me").status_code == 401

        assert client.post("/api/auth/guest").status_code == 200
        assert client.cookies["guest_id"] != old_id
