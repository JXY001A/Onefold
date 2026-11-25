"""认证与体验码接口的入参模型：邮箱归一化、验证码与密码长度约束。"""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# 只做「形状」校验，不追求 RFC 5322 全量语法：真正能用的邮箱由收信验证。
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailField(BaseModel):
    """邮箱入参基类：统一去空格 + 转小写，保证查重与登录匹配一致。"""

    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def _normalize(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_RE.match(normalized):
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