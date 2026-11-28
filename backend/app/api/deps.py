"""请求身份解析：登录用户走 JWT，访客走 guest_id Cookie。"""

from dataclasses import dataclass
from datetime import datetime, timezone

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import GuestSession, User, as_utc
from ..roles import OwnerKind, Role, owner_key_for

# 角色取值见 app/roles.py 的 Role 枚举；权限比较一律用白名单（require_role），
# 不做"等级大小"比较，避免漏改。


@dataclass(frozen=True)
class Principal:
    """一次请求的身份：登录用户或独立访客。"""
    # 身份种类用 OwnerKind 枚举，与 owner_key 前缀共用同一词表
    kind: OwnerKind
    id: str
    # 有效角色：游客固定为 guest，登录用户取自 users.role
    role: str = Role.GUEST

    # @property 是 Python 内置装饰器：作用是把方法包装成「属性」——调用时不写括号,看起来就像在读取一个数据字段,实际上背后执行的是方法。
    @property
    def lock_key(self) -> str:
        # 带上 kind 前缀，避免用户 id 与访客 id 意外碰撞
        return owner_key_for(self.kind, self.id)

    @property
    def user_id(self) -> str | None:
        return self.id if self.kind == OwnerKind.USER else None

    @property
    def owner_key(self) -> str:
        """业务归属键：会话、访问记录都按它归档（"user:xxx" / "guest:xxx"）。

        与 lock_key 取值相同，但语义不同：lock_key 用于并发锁，
        owner_key 用于「这条数据属于谁」。分开命名是为了将来加锁策略变化时不牵连数据归属。
        """
        return self.lock_key


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
        # 角色故意不写进 JWT：每次回表查，改角色/停用账号能立即生效
        user = db.get(User, str(payload["sub"]))
        if user is None:
            raise HTTPException(401, "登录已失效")
        if user.status != "active":
            raise HTTPException(401, "账号已停用")
        # 改密后旧 JWT 立即作废：iat 早于 password_changed_at 即改密前签发
        issued_at = payload.get("iat")
        if (
            user.password_changed_at is not None
            and issued_at is not None
            and int(issued_at) < as_utc(user.password_changed_at).timestamp()
        ):
            raise HTTPException(401, "密码已修改，请重新登录")
        return Principal(OwnerKind.USER, user.id, user.role)

    # 访客身份只认 Cookie + 数据库记录；客户端无法伪造一个不存在的 id
    guest_id = request.cookies.get("guest_id")
    # 读数据库检查会话存在且未过期
    guest = db.get(GuestSession, guest_id) if guest_id else None
    if not guest or as_utc(guest.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(401, "访客会话已过期")

    return Principal(OwnerKind.GUEST, guest.id)


def require_role(*roles: str):
    """生成一个校验依赖：只允许指定角色访问。

    用法：Depends(require_role(Role.ADMIN, Role.SUPERADMIN))
    无身份 → 401（未登录/访客过期）；有身份但角色不够 → 403。
    """
    allowed = set(roles)

    def checker(principal: Principal = Depends(current_principal)) -> Principal:
        if principal.role not in allowed:
            raise HTTPException(403, "权限不足")
        return principal

    return checker
