"""认证与体验码申请（骨架）。"""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import AccessRequest, GuestSession
from .deps import Principal, as_utc, current_principal

router = APIRouter()

GUEST_TTL_HOURS = 24


class AccessRequestIn(BaseModel):
    name: str
    contact: str | None = None
    purpose: str | None = None


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/request")
def create_request(body: AccessRequestIn, db: Session = Depends(get_db)):
    req = AccessRequest(
        id=str(uuid4()),
        name=body.name,
        contact=body.contact,
        purpose=body.purpose,
        status="pending",
    )
    db.add(req)
    db.commit()
    return {"request_id": req.id, "status": req.status}


@router.get("/request/{request_id}")
def get_request(request_id: str, db: Session = Depends(get_db)):
    req = db.get(AccessRequest, request_id)
    if not req:
        raise HTTPException(404, "request not found")
    return {
        "request_id": req.id,
        "status": req.status,
        "code": req.code if req.status == "approved" else None,
    }


@router.post("/login")
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    # TODO: 校验密码、签发 JWT、写 HttpOnly Cookie
    raise HTTPException(501, "login not implemented in skeleton")


@router.get("/me")
def me(principal: Principal = Depends(current_principal)):
    return {"kind": principal.kind}


@router.post("/guest")
def guest(request: Request, response: Response, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    guest_id = request.cookies.get("guest_id")
    row = db.get(GuestSession, guest_id) if guest_id else None

    # 复用未过期 Cookie，避免每次刷新页面都新建一条访客记录
    if row is None or as_utc(row.expires_at) <= now:
        guest_id = secrets.token_urlsafe(24)
        row = GuestSession(
            id=guest_id,
            ip=request.client.host if request.client else None,
            user_agent=(request.headers.get("user-agent") or "")[:255] or None,
            created_at=now,
            last_seen_at=now,
            expires_at=now + timedelta(hours=GUEST_TTL_HOURS),
        )
        db.add(row)
    else:
        row.last_seen_at = now

    db.commit()

    # HttpOnly 防 XSS 读取；Secure 由部署环境控制，线上 HTTPS 必须为 True
    response.set_cookie(
        "guest_id",
        guest_id,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=GUEST_TTL_HOURS * 3600,
        path="/",
    )
    return {"kind": "guest", "expires_in": GUEST_TTL_HOURS * 3600}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("guest_id")
    response.delete_cookie("access_token")
    return {"ok": True}
