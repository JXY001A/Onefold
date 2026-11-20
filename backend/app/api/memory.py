"""用户记忆管理 API：查看、编辑、删除、开关。"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..services.memory import (
    clear_memory,
    delete_memory_item,
    list_memory,
    set_memory_enabled,
    update_memory_item,
)
from .deps import Principal, current_principal

router = APIRouter()


class MemoryUpdateIn(BaseModel):
    # None 表示不修改；value 只对卡片生效
    text: str | None = None
    value: Any | None = None
    # 是否用户手动要求保存
    pinned: bool | None = None


class MemorySettingIn(BaseModel):
    enabled: bool


@router.get("")
def get_memory(principal: Principal = Depends(current_principal)):
    """当前身份的记忆列表；游客与登录用户使用同一接口。"""
    return list_memory(principal.owner_key)


# 注意：/settings 必须定义在 /{item_id} 之前，否则会被当成 item_id
@router.patch("/settings")
def update_settings(
    body: MemorySettingIn,
    principal: Principal = Depends(current_principal),
):
    set_memory_enabled(principal.owner_key, body.enabled)
    return {"ok": True, "enabled": body.enabled}


@router.patch("/{item_id}")
def update_item(
    item_id: str,
    body: MemoryUpdateIn,
    principal: Principal = Depends(current_principal),
):
    item = update_memory_item(
        principal.owner_key,
        item_id,
        text=body.text,
        value=body.value,
        pinned=body.pinned,
    )
    if item is None:
        raise HTTPException(404, "记忆不存在")
    return item


@router.delete("")
def clear_all(principal: Principal = Depends(current_principal)):
    return {"ok": True, "deleted": clear_memory(principal.owner_key)}


@router.delete("/{item_id}")
def delete_item(item_id: str, principal: Principal = Depends(current_principal)):
    if not delete_memory_item(principal.owner_key, item_id):
        raise HTTPException(404, "记忆不存在")
    return {"ok": True}
