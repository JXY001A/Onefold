"""认证与体验码申请（骨架）。"""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AccessRequest

router = APIRouter()


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


@router.post("/guest")
def guest(response: Response):
    # TODO: 持久化访客 session，设置 24h 过期与 IP 限流
    guest_id = str(uuid4())
    response.set_cookie("guest_id", guest_id, httponly=True, samesite="lax")
    return {"guest_id": guest_id, "expires_in": 86400}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("guest_id")
    response.delete_cookie("access_token")
    return {"ok": True}
