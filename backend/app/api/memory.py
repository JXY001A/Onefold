"""用户记忆管理 API：查看、编辑、删除、开关。

路由前缀不写在这里，而是在 main.py 的 include_router 里注入：
    app.include_router(memory.router, prefix="/api/memory")
所以下面的 @router.get("") 最终就是 /api/memory。

方法选择：读用 GET，局部改用 PATCH（不是 PUT），删除用 DELETE；
所有写操作完成后都要让会话记忆快照失效，否则下一轮会继续用旧记忆。
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..services.memory import (
    clear_memory,
    delete_memory_item,
    invalidate_memory_snapshots,
    list_memory,
    set_memory_enabled,
    update_memory_item,
)
from .deps import Principal, current_principal

router = APIRouter()  # 自身不带 prefix，prefix 由 main.py 注入


class MemoryUpdateIn(BaseModel):
    # PATCH 的典型写法：三个字段全部可选，None = 本次不改这个字段
    # （如果改用 PUT，漏传的字段会被当成“置空”，容易误删数据）
    text: str | None = None
    value: Any | None = None
    # 是否用户手动要求保存
    pinned: bool | None = None


class MemorySettingIn(BaseModel):
    enabled: bool


# path 为空串 = 直接用 prefix 本身，最终路径 /api/memory（末尾不带斜杠，
# 避免前端请求被 307 重定向）；GET 只读不改数据，可安全缓存与重试
@router.get("")
def get_memory(principal: Principal = Depends(current_principal)):
    """当前身份的记忆列表；游客与登录用户使用同一接口。"""
    return list_memory(principal.owner_key)


# 注意：/settings 必须定义在 /{item_id} 之前，否则会被当成 item_id
# 用 PATCH 不用 PUT：只改 enabled 这一个字段，其余配置保持原样
@router.patch("/settings")
def update_settings(
    body: MemorySettingIn,
    principal: Principal = Depends(current_principal),
):
    set_memory_enabled(principal.owner_key, body.enabled)
    # 开启/关闭 后用户历史记忆快照将被标记为无效
    invalidate_memory_snapshots(principal.owner_key)
    return {"ok": True, "enabled": body.enabled}


# PATCH /{item_id}：局部更新，请求体里没传的字段保持原值
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
    invalidate_memory_snapshots(principal.owner_key)
    return item


# DELETE 不带路径参数 = 清空全部。不用 body 传 id 列表：
# 很多网关/客户端会丢弃 DELETE 的请求体，用路径表达范围才可靠
@router.delete("")
def clear_all(principal: Principal = Depends(current_principal)):
    deleted = clear_memory(principal.owner_key)
    invalidate_memory_snapshots(principal.owner_key)
    return {"ok": True, "deleted": deleted}


# DELETE /{item_id}：幂等，重复删除第二次因查不到而返回 404
@router.delete("/{item_id}")
def delete_item(item_id: str, principal: Principal = Depends(current_principal)):
    if not delete_memory_item(principal.owner_key, item_id):
        raise HTTPException(404, "记忆不存在")
    invalidate_memory_snapshots(principal.owner_key)
    return {"ok": True}
