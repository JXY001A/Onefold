"""文档元数据与任务队列的数据库操作。"""

from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..models import Chunk, Document, DocumentJob, now
from .knowledge_access import PUBLIC_KB_ID

ALLOWED_SUFFIXES = {".pdf", ".md", ".markdown", ".txt", ".docx"}


def count_owned(db: Session, owner_key: str) -> int:
    stmt = select(func.count(Document.id)).where(Document.owner_key == owner_key)
    return int(db.execute(stmt).scalar_one())


def list_owned(db: Session, owner_key: str) -> list[Document]:
    return list(
        db.execute(
            select(Document)
            .where(Document.owner_key == owner_key)
            .order_by(Document.created_at.desc())
        ).scalars()
    )


def get_owned(db: Session, document_id: str, owner_key: str) -> Document | None:
    doc = db.get(Document, document_id)
    if doc is None or doc.owner_key != owner_key:
        return None
    return doc


def list_public(db: Session) -> list[Document]:
    return list(
        db.execute(
            select(Document)
            .where(Document.kb_id == PUBLIC_KB_ID, Document.status != "deleted")
            .order_by(Document.created_at.desc())
        ).scalars()
    )


def get_public(db: Session, document_id: str) -> Document | None:
    doc = db.get(Document, document_id)
    return doc if doc is not None and doc.kb_id == PUBLIC_KB_ID else None


def create_document(
    db: Session,
    *,
    document_id: str,
    kb_id: str,
    owner_key: str,
    user_id: str | None,
    conversation_id: str | None,
    filename: str,
    path: str,
    size: int,
    mime: str | None,
    expires_at,
    kind: str = "temp",
) -> Document:
    """保存元数据并入队；原始文件已由 API 写入磁盘。"""
    doc = Document(
        id=document_id,
        kb_id=kb_id,
        owner_key=owner_key,
        user_id=user_id,
        conversation_id=conversation_id,
        filename=filename,
        path=path,
        size=size,
        mime=mime,
        kind=kind,
        status="uploaded",
        expires_at=expires_at,
    )
    db.add(doc)
    db.flush()
    db.add(
        DocumentJob(
            id=str(uuid4()),
            document_id=doc.id,
            owner_key=owner_key,
            status="pending",
            stage="upload",
            run_after=now(),
            created_at=now(),
        )
    )
    db.commit()
    return doc


def remove_document(db: Session, doc: Document) -> None:
    """删除派生数据、原文件和元数据；顺序先派生后原文件。"""
    db.execute(delete(Chunk).where(Chunk.document_id == doc.id))
    db.execute(delete(DocumentJob).where(DocumentJob.document_id == doc.id))
    Path(doc.path).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()


def collect_document(db: Session, doc: Document) -> None:
    doc.kind = "personal"
    doc.expires_at = None
    db.commit()


def cleanup_expired(db: Session) -> int:
    """清理过期的临时文档；个人文档 expires_at 为 NULL，不受影响。"""
    docs = list(
        db.execute(
            select(Document).where(
                Document.kind == "temp",
                Document.expires_at.is_not(None),
                Document.expires_at <= now(),
            )
        ).scalars()
    )
    for doc in docs:
        remove_document(db, doc)
    return len(docs)


def retry_document(db: Session, doc: Document) -> None:
    """失败重试：文档和最近一条任务一起回到 pending。"""
    doc.status = "uploaded"
    doc.error = None
    job = db.execute(
        select(DocumentJob)
        .where(DocumentJob.document_id == doc.id)
        .order_by(DocumentJob.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if job is None:
        db.add(
            DocumentJob(
                id=str(uuid4()),
                document_id=doc.id,
                owner_key=doc.owner_key or "",
                status="pending",
                stage="retry",
                run_after=now(),
                created_at=now(),
            )
        )
    else:
        job.status = "pending"
        job.attempts = 0
        job.last_error = None
        job.run_after = now()
    db.commit()
