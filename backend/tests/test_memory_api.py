"""记忆 HTTP 接口：访客身份下的读取、开关、编辑与删除。"""

from fastapi.testclient import TestClient

from app.main import app
from app.services.memory import apply_extraction
from tests.conftest import cleanup_owner


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
            cleanup_owner(owner)