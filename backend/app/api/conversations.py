"""会话列表与历史消息查询。

两个接口都按「当前身份（登录用户 / 访客）」过滤，越权一律当作不存在处理。
"""

from fastapi import APIRouter, Depends, HTTPException

from ..services.history import (
    conversation_owned_by,
    list_conversations,
    load_conversation_messages,
)
from .deps import Principal, current_principal

router = APIRouter()

# 默认只回看最近 20 天（与访客 30 天滑动有效期配套）
DEFAULT_DAYS = 20


@router.get("/conversations")
def conversation_list(
    days: int = DEFAULT_DAYS,
    limit: int = 100,
    principal: Principal = Depends(current_principal),
):
    """近 days 天内有过活动的会话，按活跃时间倒序。"""
    days = max(1, min(days, 365))
    limit = max(1, min(limit, 200))
    return list_conversations(principal.owner_key, days=days, limit=limit)


@router.get("/conversations/{conversation_id}/messages")
def conversation_messages(
    conversation_id: str,
    limit: int = 200,
    principal: Principal = Depends(current_principal),
):
    """会话内消息（按时间正序）。

    不存在与无权统一返回 404，避免泄露「该会话是否存在」；
    写接口 /api/chat 仍用 403，因为那是「明确知道了别人的 ID 还去写」。
    """
    if not conversation_owned_by(conversation_id, principal.owner_key):
        raise HTTPException(404, "会话不存在")
    limit = max(1, min(limit, 500))
    return load_conversation_messages(conversation_id, limit=limit)