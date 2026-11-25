"""公共知识库：所有用户可读，管理员可发布/管理。"""

from pathlib import Path
from shutil import copyfileobj
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Document
from ..services.document_store import (
    ALLOWED_SUFFIXES,
    create_document,
    get_public,
    list_public,
    remove_document,
    retry_document,
)
from ..services.knowledge_access import (
    PUBLIC_KB_ID,
    PUBLIC_OWNER_KEY,
    ensure_public_kb,
    public_read_allowed,
)
from ..services.knowledge_publish import publish_public_document
from .deps import Principal, current_principal, require_role

router = APIRouter()
UPLOAD_DIR = settings.data_dir / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
require_admin = require_role("admin", "superadmin")


def _serialize(doc: Document) -> dict:
    return {
        "id": doc.id,
        "kb_id": doc.kb_id,
        "scope": "public",
        "filename": doc.filename,
        "size": doc.size,
        "kind": doc.kind,
        "status": doc.status,
        "error": doc.error,
        "page_count": doc.page_count,
        "chunk_count": doc.chunk_count,
        "expires_at": None,
    }


@router.get("/public/documents")
def list_public_documents(
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
):
    if not public_read_allowed(principal):
        raise HTTPException(403, "当前身份不能读取公共知识库")
    return [_serialize(doc) for doc in list_public(db)]


@router.get("/public/documents/{document_id}")
def get_public_document(
    document_id: str,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
):
    if not public_read_allowed(principal):
        raise HTTPException(403, "当前身份不能读取公共知识库")
    doc = get_public(db, document_id)
    if doc is None:
        raise HTTPException(404, "公共文档不存在")
    return _serialize(doc)


@router.post("/public/documents")
async def upload_public_document(
    file: UploadFile = File(...),
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """管理员上传公共文档；不占个人额度，不过期。"""
    safe_name = Path(file.filename or "upload.bin").name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(415, "只支持 PDF / Markdown / DOCX / TXT")
    doc_id = str(uuid4())
    dest = UPLOAD_DIR / f"public_{doc_id}_{safe_name}"
    try:
        with dest.open("wb") as target:
            copyfileobj(file.file, target)
        if dest.stat().st_size > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"文件超过 {settings.max_upload_mb} MB")
        kb = ensure_public_kb(db)
        doc = create_document(
            db,
            document_id=doc_id,
            kb_id=kb.id,
            owner_key=PUBLIC_OWNER_KEY,
            user_id=principal.id,
            conversation_id=None,
            filename=safe_name,
            path=str(dest),
            size=dest.stat().st_size,
            mime=file.content_type,
            expires_at=None,
            kind="public",
        )
        return _serialize(doc)
    except Exception:
        dest.unlink(missing_ok=True)
        raise


@router.delete("/public/documents/{document_id}")
def delete_public_document(
    document_id: str,
    _admin: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    doc = get_public(db, document_id)
    if doc is None:
        raise HTTPException(404, "公共文档不存在")
    remove_document(db, doc)
    return {"ok": True}


@router.post("/public/documents/{document_id}/retry")
def retry_public_document(
    document_id: str,
    _admin: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    doc = get_public(db, document_id)
    if doc is None:
        raise HTTPException(404, "公共文档不存在")
    retry_document(db, doc)
    return _serialize(doc)


@router.post("/public/publish/{document_id}")
def publish_document(
    document_id: str,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """管理员把个人/临时文档复制发布到公共库；原文档保留。"""
    source = db.get(Document, document_id)
    if source is None:
        raise HTTPException(404, "源文档不存在")
    if source.kb_id == PUBLIC_KB_ID or source.kind == "public":
        raise HTTPException(409, "文档已经在公共知识库")
    try:
        doc = publish_public_document(db, source, principal.id, UPLOAD_DIR)
    except FileNotFoundError as exc:
        raise HTTPException(404, "源文件不存在，无法发布") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _serialize(doc)
