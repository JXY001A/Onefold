"""请求身份解析：登录用户走 JWT，访客走 guest_id Cookie。"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import GuestSession


@dataclass(frozen=True)
class Principal:
    """一次请求的身份：登录用户或独立访客。"""
    # 相当于 ts 中的联合字段，kind：'user' | 'guest';
    kind: Literal["user", "guest"]
    id: str

    # @property 是 Python 内置装饰器：作用是把方法包装成「属性」——调用时不写括号,看起来就像在读取一个数据字段,实际上背后执行的是方法。
    @property
    def lock_key(self) -> str:
        # 带上 kind 前缀，避免用户 id 与访客 id 意外碰撞
        return f"{self.kind}:{self.id}"

    @property
    def user_id(self) -> str | None:
        return self.id if self.kind == "user" else None


def as_utc(value: datetime) -> datetime:
    # SQLite 不保存时区，读出来是 naive datetime
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def current_principal(
    request: Request,
    # 当调用 current_principal 时，FastAPI 会自动注入当前请求的数据库会话
    db: Session = Depends(get_db),
) -> Principal:
    # 登录用户优先：JWT 自带 exp/sub，不依赖服务端会话表
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=["HS256"],
                options={"require": ["exp", "sub"]},
            )
        except jwt.InvalidTokenError as exc:
            raise HTTPException(401, "登录已失效") from exc
        # JWT 自带 exp/sub，不依赖服务端会话表
        return Principal("user", str(payload["sub"]))

    # 访客身份只认 Cookie + 数据库记录；客户端无法伪造一个不存在的 id
    guest_id = request.cookies.get("guest_id")
    # 读数据库检查会话存在且未过期
    guest = db.get(GuestSession, guest_id) if guest_id else None
    if not guest or as_utc(guest.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(401, "访客会话已过期")

    return Principal("guest", guest.id)
