"""文档上传、状态查询与管理；归属统一走 current_principal。"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from shutil import copyfileobj
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Document
from ..services.document_store import (
    ALLOWED_SUFFIXES,
    collect_document,
    count_owned,
    create_document,
    get_owned,
    list_owned,
    remove_document,
    retry_document,
)
from ..services.history import conversation_owned_by
from ..services.knowledge_access import get_or_create_personal_kb
from .deps import Principal, current_principal

router = APIRouter()
UPLOAD_DIR = settings.data_dir / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DAYS = 7


def _limit(principal: Principal) -> int:
    return settings.guest_docs_max if principal.kind == "guest" else settings.user_docs_max


def _serialize(doc: Document) -> dict:
    return {
        "id": doc.id,
        "kb_id": doc.kb_id,
        "scope": "temp" if doc.kind == "temp" else "personal",
        "filename": doc.filename,
        "size": doc.size,
        "kind": doc.kind,
        "status": doc.status,
        "error": doc.error,
        "page_count": doc.page_count,
        "chunk_count": doc.chunk_count,
        "expires_at": doc.expires_at.isoformat() if doc.expires_at else None,
    }


@router.post("")
async def upload(
    file: UploadFile = File(...),
    conversation_id: str | None = Form(None),
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
):
    """保存原件到磁盘，写元数据与 document_jobs，等待 index-worker。"""
    safe_name = Path(file.filename or "upload.bin").name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(415, "只支持 PDF / Markdown / DOCX / TXT")
    if conversation_id and not conversation_owned_by(conversation_id, principal.owner_key):
        raise HTTPException(403, "无权访问该会话")
    if count_owned(db, principal.owner_key) >= _limit(principal):
        raise HTTPException(403, "文档数量已达上限")

    doc_id = str(uuid4())
    dest = UPLOAD_DIR / f"{doc_id}_{safe_name}"
    try:
        with dest.open("wb") as target:
            copyfileobj(file.file, target)
        if dest.stat().st_size > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"文件超过 {settings.max_upload_mb} MB")
        kb = get_or_create_personal_kb(db, principal.owner_key)
        doc = create_document(
            db,
            document_id=doc_id,
            kb_id=kb.id,
            owner_key=principal.owner_key,
            user_id=principal.user_id,
            conversation_id=conversation_id,
            filename=safe_name,
            path=str(dest),
            size=dest.stat().st_size,
            mime=file.content_type,
            expires_at=datetime.now(timezone.utc) + timedelta(days=TEMP_DAYS),
        )
        return _serialize(doc)
    except Exception:
        dest.unlink(missing_ok=True)
        raise


@router.get("")
def list_documents(
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
):
    return [_serialize(doc) for doc in list_owned(db, principal.owner_key)]


@router.get("/{doc_id}")
def get_document(
    doc_id: str,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
):
    doc = get_owned(db, doc_id, principal.owner_key)
    if doc is None:
        raise HTTPException(404, "文档不存在")
    return _serialize(doc)


@router.delete("/{doc_id}")
def delete_document(
    doc_id: str,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
):
    doc = get_owned(db, doc_id, principal.owner_key)
    if doc is None:
        raise HTTPException(404, "文档不存在")
    remove_document(db, doc)
    return {"ok": True}


@router.post("/{doc_id}/collect")
def collect(
    doc_id: str,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
):
    if principal.kind != "user":
        raise HTTPException(403, "登录后才能收藏文档")
    doc = get_owned(db, doc_id, principal.owner_key)
    if doc is None:
        raise HTTPException(404, "文档不存在")
    collect_document(db, doc)
    return {"ok": True, "kind": doc.kind}


@router.post("/{doc_id}/retry")
def retry(
    doc_id: str,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
):
    doc = get_owned(db, doc_id, principal.owner_key)
    if doc is None:
        raise HTTPException(404, "文档不存在")
    retry_document(db, doc)
    return _serialize(doc)
