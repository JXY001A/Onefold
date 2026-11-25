"""管理员发布：把个人/临时文档复制成公共知识库文档。

默认复制而不是原地移动：个人文档保留，公共副本独立索引，用户删除自己的
文档不会影响公共库。发布动作写 audit_logs，记录发布人和来源。
"""

from pathlib import Path
from shutil import copy2
from uuid import uuid4

from sqlalchemy.orm import Session

from ..models import AuditLog, Document, DocumentJob, now
from .knowledge_access import PUBLIC_OWNER_KEY, ensure_public_kb


def publish_public_document(
    db: Session,
    source: Document,
    admin_id: str | None,
    upload_dir: Path,
) -> Document:
    """复制源文件并创建一条 public 文档；返回新文档。"""
    if source.kb_id == "public" or source.kind == "public":
        raise ValueError("文档已经在公共知识库")
    kb = ensure_public_kb(db)
    new_id = str(uuid4())
    safe_name = Path(source.filename).name
    dest = upload_dir / f"public_{new_id}_{safe_name}"

    try:
        copy2(source.path, dest)
        public_doc = Document(
            id=new_id,
            kb_id=kb.id,
            owner_key=PUBLIC_OWNER_KEY,
            user_id=admin_id,
            conversation_id=None,
            filename=safe_name,
            path=str(dest),
            size=dest.stat().st_size,
            mime=source.mime,
            kind="public",
            status="uploaded",
            content_hash=source.content_hash,
            expires_at=None,
        )
        db.add(public_doc)
        db.flush()
        db.add(
            DocumentJob(
                id=str(uuid4()),
                document_id=public_doc.id,
                owner_key=PUBLIC_OWNER_KEY,
                status="pending",
                stage="publish",
                run_after=now(),
                created_at=now(),
            )
        )
        db.add(
            AuditLog(
                id=str(uuid4()),
                user_id=admin_id,
                action="publish_public_document",
                target=source.id,
                detail_json={
                    "public_document_id": public_doc.id,
                    "source_kb_id": source.kb_id,
                    "source_owner_key": source.owner_key,
                },
            )
        )
        db.commit()
        return public_doc
    except Exception:
        db.rollback()
        dest.unlink(missing_ok=True)
        raise
