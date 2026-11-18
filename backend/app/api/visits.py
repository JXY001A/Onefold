"""访问记录接口：进入 / 心跳 / 离开。

身份来自 current_principal（登录用户 JWT 或访客 Cookie），所以拿不到身份时
前端应先调 /api/auth/guest 建访客身份，再上报访问记录。
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..services.visits import end_visit, record_visit, touch_visit
from .deps import Principal, current_principal

router = APIRouter()


class VisitIn(BaseModel):
    """进入页面时前端上报的客户端信息（服务端拿不到的部分）。"""

    path: str | None = None
    referrer: str | None = None
    screen: str | None = None
    language: str | None = None
    timezone: str | None = None


@router.post("/enter")
def enter(
    body: VisitIn,
    request: Request,
    principal: Principal = Depends(current_principal),
):
    """记录一次进入，返回 visit_id 供心跳与离开复用。"""
    return record_visit(principal, request, body.model_dump())


@router.post("/{visit_id}/heartbeat")
def heartbeat(visit_id: str, principal: Principal = Depends(current_principal)):
    """刷新活跃时间；不是自己的记录返回 ok=false。"""
    return {"ok": touch_visit(visit_id, principal.owner_key)}


@router.post("/{visit_id}/leave")
def leave(visit_id: str, principal: Principal = Depends(current_principal)):
    """记录离开时间与停留时长；不是自己的记录返回 ok=false。"""
    return {"ok": end_visit(visit_id, principal.owner_key)}