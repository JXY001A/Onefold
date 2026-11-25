"""访客数据收养的回归测试：仅注册迁移、登录不迁移、注册后 guest_id 轮换。"""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import Conversation, MemorySetting

PASSWORD = "passw0rd123"


def _email() -> str:
    return f"{uuid4().hex[:10]}@example.com"


def _register(client: TestClient, email: str) -> dict:
    """走验证码 + 注册，返回注册响应体（dev 模式会回传 dev_code）。"""
    got = client.post("/api/auth/email-code", json={"email": email, "purpose": "register"})
    assert got.status_code == 200, got.text
    res = client.post(
        "/api/auth/register",
        json={"email": email, "code": got.json()["dev_code"], "password": PASSWORD},
    )
    assert res.status_code == 200, res.text
    return res.json()


def _seed_conversation(owner_key: str) -> str:
    """直接往库里塞一条会话：比真跑一轮对话快，也不依赖模型可用性。"""
    cid = str(uuid4())
    with SessionLocal() as db:
        db.add(Conversation(id=cid, owner_key=owner_key, title="游客时期的会话"))
        db.commit()
    return cid


def test_register_adopts_guest_data_and_rotates_cookie():
    with TestClient(app) as client:
        assert client.post("/api/auth/guest").status_code == 200
        guest_id = client.cookies["guest_id"]
        cid = _seed_conversation(f"guest:{guest_id}")

        # 开关表是主键，需要整行搬迁而不是 UPDATE
        with SessionLocal() as db:
            db.add(MemorySetting(owner_key=f"guest:{guest_id}", enabled=False))
            db.commit()

        uid = _register(client, _email())["id"]

        with SessionLocal() as db:
            assert db.get(Conversation, cid).owner_key == f"user:{uid}"
            assert db.get(MemorySetting, f"guest:{guest_id}") is None
            assert db.get(MemorySetting, f"user:{uid}").enabled is False

        # 注册响应必须作废旧 guest_id，否则登出后的游客数据会再写回旧归属
        assert "guest_id" not in client.cookies

        # 再以访客身份访问拿到的是全新 id，与账号历史互不相干
        assert client.post("/api/auth/guest").status_code == 200
        assert client.cookies["guest_id"] != guest_id


def test_login_does_not_adopt_guest_data():
    email = _email()
    with TestClient(app) as client:
        _register(client, email)

        # 退出后以游客身份留一条会话，再登录：这条会话必须留在 guest 名下
        assert client.post("/api/auth/logout").status_code == 200
        assert client.post("/api/auth/guest").status_code == 200
        guest_id = client.cookies["guest_id"]
        cid = _seed_conversation(f"guest:{guest_id}")

        res = client.post("/api/auth/login", json={"account": email, "password": PASSWORD})
        assert res.status_code == 200, res.text

        with SessionLocal() as db:
            assert db.get(Conversation, cid).owner_key == f"guest:{guest_id}"


def test_register_without_guest_cookie_still_works():
    """没有访客身份直接注册：跳过迁移，不能报错。"""
    with TestClient(app) as client:
        assert client.post("/api/auth/guest").status_code == 200
        client.cookies.delete("guest_id")

        assert _register(client, _email())["kind"] == "user"