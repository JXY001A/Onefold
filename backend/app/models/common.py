"""模型共用的声明基类、列类型与时间工具。

各表按业务域分文件（account / chat / document / memory），
统一由 __init__ 重新导出，调用方仍然只写 `from ..models import X`。
"""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    text as sql_text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """数据库读出的时间可能不带时区，统一按 UTC 处理后再参与计算。"""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


__all__ = [
    "Base",
    "JSON",
    "JSONB",
    "Boolean",
    "DateTime",
    "Float",
    "Index",
    "Integer",
    "Mapped",
    "String",
    "Text",
    "as_utc",
    "mapped_column",
    "now",
    "sql_text",
]