"""知识库作用域与管理员发布的回归测试。"""

from pathlib import Path
from uuid import uuid4

from app.api.deps import Principal
from app.config import settings
from app.models import Document, KnowledgeBase
from app.services.knowledge_access import (
    can_write_kb,
    public_read_allowed,
    scope_label,
)
from app.services.knowledge_publish import publish_public_document


class FakeDB:
    """只实现发布服务需要的 Session 方法。"""

    def __init__(self):
        self.added = []
        self.public_kb = None

    def get(self, model, key):
        if model is KnowledgeBase and key == "public":
            return self.public_kb
        return None

    def add(self, obj):
        self.added.append(obj)
        if isinstance(obj, KnowledgeBase):
            self.public_kb = obj

    def flush(self):
        return None

    def commit(self):
        return None

    def rollback(self):
        return None


def test_scope_permissions_and_labels():
    user = Principal("user", "u1", "member")
    admin = Principal("user", "a1", "admin")
    public_kb = KnowledgeBase(id="public", kind="public", name="公共", owner_key=None)
    personal_kb = KnowledgeBase(id="p1", kind="personal", name="个人", owner_key="user:u1")

    assert not can_write_kb(user, public_kb)
    assert can_write_kb(admin, public_kb)
    assert can_write_kb(user, personal_kb)
    assert not can_write_kb(admin, personal_kb)
    assert scope_label(public_kb, "public") == "公共知识库"
    assert scope_label(personal_kb, "temp") == "临时文档"
    assert scope_label(personal_kb, "personal") == "个人知识库"


def test_public_read_guest_switch(monkeypatch):
    guest = Principal("guest", "g1")
    monkeypatch.setattr(settings, "public_kb_guest_read", True)
    assert public_read_allowed(guest)
    monkeypatch.setattr(settings, "public_kb_guest_read", False)
    assert not public_read_allowed(guest)
    assert public_read_allowed(Principal("user", "u1", "member"))


def test_publish_copies_file_and_keeps_source(tmp_path: Path):
    source_file = tmp_path / "source.md"
    source_file.write_text("private knowledge", encoding="utf-8")
    source = Document(
        id=str(uuid4()),
        kb_id="personal-kb",
        owner_key="user:u1",
        filename="source.md",
        path=str(source_file),
        size=source_file.stat().st_size,
        mime="text/markdown",
        kind="personal",
        status="ready",
        content_hash="hash",
    )
    db = FakeDB()

    public = publish_public_document(db, source, "admin-1", tmp_path)

    assert source_file.exists()
    assert public.kb_id == "public"
    assert public.owner_key == "public"
    assert public.kind == "public"
    assert public.conversation_id is None
    assert Path(public.path).exists()
    assert Path(public.path).read_text(encoding="utf-8") == "private knowledge"
    assert source.kb_id == "personal-kb"
    assert any(type(item).__name__ == "AuditLog" for item in db.added)
