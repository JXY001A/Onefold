"""记忆作用域：owner_key 身份解析，以及「全局 + 单用户」两级开关。"""

from ..config import settings
from ..db import SessionLocal
from ..models import MemorySetting, now


def owner_kind(owner_key: str) -> str:
    """从 user:<id> / guest:<id> 取身份类型。"""
    return "guest" if owner_key.startswith("guest:") else "user"


def memory_enabled_for(owner_key: str) -> bool:
    """两级开关：全局配置与单用户设置都为真才启用。

    用户没建过 settings 行时默认开启，省掉首次写库。
    """
    if not settings.memory_enabled:
        return False
    db = SessionLocal()
    try:
        row = db.get(MemorySetting, owner_key)
        return row.enabled if row else True
    finally:
        db.close()


def set_memory_enabled(owner_key: str, enabled: bool) -> None:
    """写入单用户开关：已有记录就更新，没有就新建一行。"""
    db = SessionLocal()
    try:
        row = db.get(MemorySetting, owner_key)
        if row is None:
            row = MemorySetting(owner_key=owner_key, enabled=enabled, updated_at=now())
            db.add(row)
        else:
            row.enabled = enabled
            row.updated_at = now()
        db.commit()
    finally:
        db.close()