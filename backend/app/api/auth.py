"""认证：访客身份、邮箱注册登录、验证码重置密码、体验码申请。

账号以邮箱为主（email 唯一），username 只作展示昵称；
早期没有邮箱的账号（如手动写入的超管）仍可用用户名登录。
验证码只存哈希；SMTP 未配置时走 dev 模式（码写日志 + 响应回传）。
"""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import User
from ..services import email_codes, guest_data, mail
from ..services.auth_session import (
    client_ip,
    guest_quota,
    set_auth_cookie,
    unique_username,
    user_payload,
)
from ..services.email_codes import InvalidCode, TooManyRequests
from .auth_schemas import EmailIn, LoginIn, RegisterIn, ResetIn
from .deps import Principal, current_principal

router = APIRouter()
log = logging.getLogger("onefold.auth")

# 密码哈希：argon2（自带随机盐与可调成本，比 bcrypt 更新）
_pwd = CryptContext(schemes=["argon2"], deprecated="auto")


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
        code = email_codes.issue(db, body.email, body.purpose, client_ip(request))
    except TooManyRequests as exc:
        raise HTTPException(429, str(exc)) from exc

    try:
        mail.send_code(body.email, code, body.purpose)
    except Exception as exc:  # SMTP 抖动：给用户明确提示，细节只进日志
        log.exception("发送验证码失败: %s", body.email)
        raise HTTPException(502, "验证码发送失败，请稍后重试") from exc

    payload = {"ok": True, "expires_in": settings.email_code_ttl_minutes * 60}
    # 仅本地（非 prod）且未配 SMTP 时回传验证码，方便直接联调；
    # 生产环境即使 SMTP 被误清空也绝不回传，否则等于把任意邮箱的验证码公开
    if settings.env != "prod" and mail.dev_mode():
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
        username=unique_username(db, body.username or body.email.split("@")[0]),
        email=body.email,
        password_hash=_pwd.hash(body.password),
        role="member",
        status="active",
    )
    db.add(user)
    db.flush()  # 先拿到 user.id，迁移访客数据时要用它拼 user:<id>
    guest_id = request.cookies.get("guest_id")
    if guest_id:
        guest_data.adopt_guest(db, guest_id, user.id)
    db.commit()
    set_auth_cookie(response, user)
    # 旧 guest_id 立即作废：之后再以访客身份访问会拿到全新 id，不与账号历史交叉
    guest_data.rotate_guest_cookie(response)
    return user_payload(user)


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
    # 登录不收养访客数据：公用浏览器下，前一个人的游客记录不能被后一个登录者看到
    db.commit()
    set_auth_cookie(response, user)
    return user_payload(user)


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
            "quota": guest_quota(principal.role, principal.owner_key),
        }

    user = db.get(User, principal.id)
    if user is None:
        raise HTTPException(401, "登录已失效")
    return user_payload(user)


# 访客登录，通过设置 guest_id Cookie,来实现访客的记录
@router.post("/guest")
def guest(request: Request, response: Response, db: Session = Depends(get_db)):
    """确保浏览器有一个未过期的访客身份，并写进 HttpOnly Cookie。"""
    return {"kind": "guest", "expires_in": guest_data.issue_guest(db, request, response)}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("guest_id")
    response.delete_cookie("access_token")
    return {"ok": True}