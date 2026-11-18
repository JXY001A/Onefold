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

# 30 天滑动有效期：每次进入站点（/api/auth/guest）都顺延过期时间，
# 所以「连续 30 天没来」才会失去身份，而不是从首次访问起算 30 天。
GUEST_TTL_HOURS = 24 * 30


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


# 访客登录，通过设置 guest_id Cookie,来实现访客的记录
@router.post("/guest")
def guest(request: Request, response: Response, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    guest_id = request.cookies.get("guest_id")
    row = db.get(GuestSession, guest_id) if guest_id else None
    # 计算有效期，当前时间加上 30 天
    expires_at = now + timedelta(hours=GUEST_TTL_HOURS)

    # 复用未过期 Cookie，避免每次刷新页面都新建一条访客记录；判断是否过期，过期重新生成 guest_id
    if row is None or as_utc(row.expires_at) <= now:
        guest_id = secrets.token_urlsafe(24)
        row = GuestSession(
            id=guest_id,
            ip=request.client.host if request.client else None,
            user_agent=(request.headers.get("user-agent") or "")[:255] or None,
            created_at=now,
            last_seen_at=now,
            expires_at=expires_at,
        )
        db.add(row)
    else:
        # 滑动续期：老访客每来一次就把有效期往后推 30 天
        row.last_seen_at = now
        row.expires_at = expires_at

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
