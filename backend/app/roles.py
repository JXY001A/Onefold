"""账号身份词表的唯一事实来源：角色 Role 与主体种类 OwnerKind。

背景：role / kind 都是数据库里的字符串字段（无外键约束），散写字面量曾导致
`role == "user"` 永远不成立、登录用户记忆提取永不触发的线上事故（2026-11-28）。
此后代码中禁止再出现裸的角色/种类字符串，统一引用本模块。

注意区分：LLM 消息里的 role（user/assistant/tool）是另一套词表，不在本模块。
两个枚举都用 str 混入，与数据库中已存的字符串逐一相等，无需数据迁移；
f-string 拼接时务必用 .value（f"{Role.ADMIN}" 会得到 "Role.ADMIN" 而非 "admin"）。
"""

from enum import Enum


class Role(str, Enum):
    """账号角色（users.role / Principal.role）。"""

    GUEST = "guest"
    MEMBER = "member"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class OwnerKind(str, Enum):
    """主体种类（Principal.kind / *_jobs.owner_kind / owner_key 前缀）。"""

    USER = "user"
    GUEST = "guest"


# owner_key 的固定前缀：kind 的客观依据（guest:... / user:...）
GUEST_OWNER_PREFIX = "guest:"
USER_OWNER_PREFIX = "user:"


def owner_key_for(kind: OwnerKind | str, ident: str) -> str:
    """拼业务归属键：user:<id> / guest:<id>。兼容传入裸字符串（如测试构造）。"""
    value = kind.value if isinstance(kind, OwnerKind) else str(kind)
    return f"{value}:{ident}"


def is_guest(value: str) -> bool:
    """账号角色是否为访客。"""
    return value == Role.GUEST


def is_admin(value: str) -> bool:
    """角色是否具备后台权限（管理员 / 超管）。"""
    return value in (Role.ADMIN, Role.SUPERADMIN)
