"""文档上传与管理（骨架）。"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from shutil import copyfileobj
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Document

router = APIRouter()

UPLOAD_DIR = settings.data_dir / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("")
async def upload(
    file: UploadFile = File(...),
    user_id: str | None = None,
    db: Session = Depends(get_db),
):
    safe_name = Path(file.filename or "upload.bin").name
    doc_id = str(uuid4())
    dest = UPLOAD_DIR / f"{doc_id}_{safe_name}"

    with dest.open("wb") as f:
        copyfileobj(file.file, f)

    if dest.stat().st_size > settings.max_upload_mb * 1024 * 1024:
        dest.unlink(missing_ok=True)
        raise HTTPException(413, f"file exceeds {settings.max_upload_mb} MB")

    doc = Document(
        id=doc_id,
        user_id=user_id,
        filename=safe_name,
        path=str(dest),
        size=dest.stat().st_size,
        mime=file.content_type,
        kind="temp",
        status="uploaded",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(doc)
    db.commit()
    return {"id": doc.id, "status": doc.status, "filename": doc.filename}


@router.get("")
def list_documents(user_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Document)
    if user_id:
        q = q.filter(Document.user_id == user_id)
    docs = q.order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "size": d.size,
            "kind": d.kind,
            "status": d.status,
            "expires_at": d.expires_at.isoformat() if d.expires_at else None,
        }
        for d in docs
    ]


@router.delete("/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "document not found")
    Path(doc.path).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
    return {"ok": True}


@router.post("/{doc_id}/collect")
def collect_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "document not found")
    doc.kind = "personal"
    doc.expires_at = None
    db.commit()
    return {"ok": True, "kind": doc.kind}
