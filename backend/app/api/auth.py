"""认证：访客身份、邮箱注册登录、验证码重置密码、体验码申请。

账号以邮箱为主（email 唯一），username 只作展示昵称；
早期没有邮箱的账号（如手动写入的超管）仍可用用户名登录。
验证码只存哈希；SMTP 未配置时走 dev 模式（码写日志 + 响应回传）。
"""

import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from passlib.context import CryptContext
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import AccessRequest, Conversation, GuestSession, User, Visit
from ..services import email_codes, mail
from ..services.email_codes import InvalidCode, TooManyRequests
from ..services.quota import rounds_used
from .deps import Principal, as_utc, current_principal

router = APIRouter()
log = logging.getLogger("onefold.auth")

# 30 天滑动有效期：每次进入站点（/api/auth/guest）都顺延过期时间，
# 所以「连续 30 天没来」才会失去身份，而不是从首次访问起算 30 天。
GUEST_TTL_HOURS = 24 * 30

# 密码哈希：argon2（自带随机盐与可调成本，比 bcrypt 更新）
_pwd = CryptContext(schemes=["argon2"], deprecated="auto")

# 只做「形状」校验，不追求 RFC 5322 全量语法：真正能用的邮箱由收信验证。
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AccessRequestIn(BaseModel):
    name: str
    contact: str | None = None
    purpose: str | None = None


class EmailField(BaseModel):
    """邮箱入参基类：统一去空格 + 转小写，保证查重与登录匹配一致。"""

    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def _normalize(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise ValueError("邮箱格式不正确")
        return normalized


class EmailIn(EmailField):
    purpose: Literal["register", "reset"]


class RegisterIn(EmailField):
    """注册：邮箱 + 验证码 + 密码，昵称可不填（默认取 @ 前部分）。"""

    code: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=8, max_length=128)
    username: str | None = Field(default=None, max_length=32)


class LoginIn(BaseModel):
    """登录：account 含 @ 当作邮箱，否则按旧账号的用户名查。"""

    account: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class ResetIn(EmailField):
    code: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=8, max_length=128)


def _set_auth_cookie(response: Response, user: User) -> None:
    """签发 JWT 并写入 HttpOnly Cookie。

    JWT 只放 sub / iat / exp：角色每次回表查，改角色/停用账号能立即生效；
    iat 用来和 users.password_changed_at 比较，改密后旧登录态自动作废。
    """
    issued = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": user.id,
            "iat": issued,
            "exp": issued + timedelta(hours=settings.jwt_ttl_hours),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_ttl_hours * 3600,
        path="/",
    )


def _quota(principal: Principal) -> dict | None:
    """游客返回已用/上限轮次；登录用户无限量，返回 None。"""
    if principal.role != "guest":
        return None
    return {
        "used": rounds_used(principal.owner_key),
        "limit": settings.guest_max_rounds,
    }


def _user_payload(user: User) -> dict:
    """登录用户的 /me 结构，注册、登录、/me 三处复用。"""
    return {
        "id": user.id,
        "kind": "user",
        "role": user.role,
        "username": user.username,
        "email": user.email,
        "quota": None,
    }


def _adopt_guest_data(db: Session, request: Request, user: User) -> None:
    """把当前浏览器内的访客数据归到账号名下。

    注册/登录时调用：否则访客攒下的会话在换成 user 身份后就"不见了"，
    与前端「注册后继续」的文案不符；访问记录一并绑定，画像可跨身份追踪。
    """
    guest_id = request.cookies.get("guest_id")
    if not guest_id:
        return
    old, new = f"guest:{guest_id}", f"user:{user.id}"
    db.query(Conversation).filter(Conversation.owner_key == old).update(
        {Conversation.owner_key: new}, synchronize_session=False
    )
    db.query(Visit).filter(Visit.owner_key == old).update(
        {Visit.owner_key: new, Visit.kind: "user"}, synchronize_session=False
    )


def _client_ip(request: Request) -> str | None:
    host = request.client.host if request.client else None
    return host.removeprefix("::ffff:") if host else None


def _unique_username(db: Session, seed: str) -> str:
    """昵称兜底：取邮箱 @ 前部分，重名自动加 -2、-3…（username 唯一）。"""
    base = (seed.strip() or "user")[:32]
    candidate = base
    for i in range(2, 1000):
        if db.query(User.id).filter(User.username == candidate).first() is None:
            return candidate
        candidate = f"{base}-{i}"
    return f"{base}-{uuid4().hex[:6]}"


@router.post("/email-code")
def send_email_code(body: EmailIn, request: Request, db: Session = Depends(get_db)):
    """发送 6 位验证码。

    register 要求邮箱未注册（已注册就引导去登录）；
    reset 对未注册邮箱静默成功，避免被用来探测账号是否存在。
    """
    exists = db.query(User.id).filter(User.email == body.email).first() is not None
    if body.purpose == "register" and exists:
        raise HTTPException(409, "该邮箱已注册，请直接登录")
    if body.purpose == "reset" and not exists:
        return {"ok": True, "expires_in": settings.email_code_ttl_minutes * 60}

    try:
        code = email_codes.issue(db, body.email, body.purpose, _client_ip(request))
    except TooManyRequests as exc:
        raise HTTPException(429, str(exc)) from exc

    try:
        mail.send_code(body.email, code, body.purpose)
    except Exception as exc:  # SMTP 抖动：给用户明确提示，细节只进日志
        log.exception("发送验证码失败: %s", body.email)
        raise HTTPException(502, "验证码发送失败，请稍后重试") from exc

    payload = {"ok": True, "expires_in": settings.email_code_ttl_minutes * 60}
    # 本地没配 SMTP 时把码带回来，方便直接联调；配了 SMTP 就不会出现该字段
    if mail.dev_mode():
        payload["dev_code"] = code
    return payload


@router.post("/register")
def register(
    body: RegisterIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """邮箱 + 验证码 + 密码注册，成功后直接登录（角色 member）。"""
    if db.query(User.id).filter(User.email == body.email).first():
        raise HTTPException(409, "该邮箱已注册，请直接登录")
    try:
        email_codes.verify(db, body.email, "register", body.code)
    except InvalidCode as exc:
        raise HTTPException(400, str(exc)) from exc

    user = User(
        id=str(uuid4()),
        username=_unique_username(db, body.username or body.email.split("@")[0]),
        email=body.email,
        password_hash=_pwd.hash(body.password),
        role="member",
        status="active",
    )
    db.add(user)
    _adopt_guest_data(db, request, user)
    db.commit()
    _set_auth_cookie(response, user)
    return _user_payload(user)


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
def login(
    body: LoginIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """邮箱（或旧账号的用户名）+ 密码登录，成功后写入 JWT Cookie。"""
    account = body.account.strip()
    if "@" in account:
        user = db.query(User).filter(User.email == account.lower()).first()
    else:
        user = db.query(User).filter(User.username == account).first()
    # 账号不存在与密码错误返回同一句话，避免被用来枚举账号
    if user is None or not _pwd.verify(body.password, user.password_hash):
        raise HTTPException(401, "邮箱或密码错误")
    if user.status != "active":
        raise HTTPException(403, "账号已停用")
    _adopt_guest_data(db, request, user)
    db.commit()
    _set_auth_cookie(response, user)
    return _user_payload(user)


@router.post("/reset-password")
def reset_password(body: ResetIn, db: Session = Depends(get_db)):
    """邮箱验证码重置密码；成功后旧 JWT 因 iat 早于改密时间而立即失效。"""
    try:
        email_codes.verify(db, body.email, "reset", body.code)
    except InvalidCode as exc:
        raise HTTPException(400, str(exc)) from exc

    user = db.query(User).filter(User.email == body.email).first()
    if user is None:
        # 正常流程走不到：没账号就不会发出 reset 码，提示与校验失败保持一致
        raise HTTPException(400, "验证码无效或已过期")
    if user.status != "active":
        raise HTTPException(403, "账号已停用")

    user.password_hash = _pwd.hash(body.password)
    user.password_changed_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@router.get("/me")
def me(
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
):
    """当前身份：角色 + 昵称 + 邮箱 + 游客配额，前端据此渲染菜单/守卫。"""
    if principal.kind == "guest":
        return {
            "id": principal.id,
            "kind": "guest",
            "role": principal.role,
            "username": None,
            "email": None,
            "quota": _quota(principal),
        }

    user = db.get(User, principal.id)
    if user is None:
        raise HTTPException(401, "登录已失效")
    return _user_payload(user)


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