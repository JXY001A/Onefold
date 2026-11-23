"""登录态签发与身份载荷组装：JWT Cookie、昵称兜底、客户端 IP、游客配额。"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import Request, Response
from sqlalchemy.orm import Session

from ..config import settings
from ..models import User
from .quota import rounds_used


def set_auth_cookie(response: Response, user: User) -> None:
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


def user_payload(user: User) -> dict:
    """登录用户的 /me 结构，注册、登录、/me 三处复用。"""
    return {
        "id": user.id,
        "kind": "user",
        "role": user.role,
        "username": user.username,
        "email": user.email,
        "quota": None,
    }


def guest_quota(role: str, owner_key: str) -> dict | None:
    """访客返回已用/上限轮次；登录用户无限量，返回 None。"""
    if role != "guest":
        return None
    return {
        "used": rounds_used(owner_key),
        "limit": settings.guest_max_rounds,
    }


def client_ip(request: Request) -> str | None:
    """取客户端 IP，并去掉 IPv6 映射前缀，便于日志与限流按同一口径聚合。"""
    host = request.client.host if request.client else None
    return host.removeprefix("::ffff:") if host else None


def unique_username(db: Session, seed: str) -> str:
    """昵称兜底：取邮箱 @ 前部分，重名自动加 -2、-3…（username 唯一）。"""
    base = (seed.strip() or "user")[:32]
    candidate = base
    for i in range(2, 1000):
        if db.query(User.id).filter(User.username == candidate).first() is None:
            return candidate
        candidate = f"{base}-{i}"
    return f"{base}-{uuid4().hex[:6]}"