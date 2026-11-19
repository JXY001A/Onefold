"""管理后台：审批、用户、用量、run 详情、存储。

权限分两层：
    admin / superadmin  → 所有读接口（审批、用户列表、用量、run 详情、存储）
    superadmin          → 额外可改角色、停用账号（超管角色本身只能手动改库）
越权统一 403；角色变更写 audit_logs，便于事后追溯。
"""

import os
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import AccessRequest, AuditLog, Message, Run, ToolCall, UsageDaily, User
from .deps import Principal, require_role

# 使用 router 将权限相关接口统一到 /api/admin 路由下
router = APIRouter()

# 两个校验依赖：读接口要 admin 起，写角色要 superadmin
require_admin = require_role("admin", "superadmin")
require_superadmin = require_role("superadmin")


def _audit(
    db: Session,
    principal: Principal,
    action: str,
    target: str,
    detail: dict,
    request: Request,
) -> None:
    """记录敏感操作（改角色、停用账号），与业务变更在同一个事务里提交。"""
    db.add(
        AuditLog(
            id=str(uuid4()),
            user_id=principal.id,
            action=action,
            target=target,
            detail_json=detail,
            ip=request.client.host if request.client else None,
        )
    )


# 获取访问请求列表
@router.get("/requests")
def list_requests(
    _admin: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(AccessRequest).order_by(AccessRequest.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "contact": r.contact,
            "purpose": r.purpose,
            "status": r.status,
            "code": r.code,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


# 审批访问请求
@router.post("/requests/{request_id}/approve")
def approve_request(
    request_id: str,
    _admin: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    req = db.get(AccessRequest, request_id)
    if not req:
        raise HTTPException(404, "request not found")
    req.status = "approved"
    req.code = f"OF-{uuid4().hex[:8].upper()}"
    req.decided_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "code": req.code}


# 获取用户列表（不含密码哈希）
@router.get("/users")
def list_users(
    _admin: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "status": u.status,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in rows
    ]


class RoleIn(BaseModel):
    role: Literal["member", "admin"]


# 仅超管：指定/撤销管理员
@router.patch("/users/{user_id}/role")
def change_role(
    user_id: str,
    body: RoleIn,
    request: Request,
    principal: Principal = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    if user_id == principal.id:
        raise HTTPException(400, "不能修改自己的角色")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "user not found")
    if user.role == "superadmin":
        raise HTTPException(400, "不能修改超管角色")
    before = user.role
    user.role = body.role
    _audit(db, principal, "role_change", user_id, {"from": before, "to": body.role}, request)
    db.commit()
    return {"ok": True, "id": user_id, "role": user.role}


class StatusIn(BaseModel):
    status: Literal["active", "disabled"]


# 仅超管：停用/启用账号
@router.patch("/users/{user_id}/status")
def change_status(
    user_id: str,
    body: StatusIn,
    request: Request,
    principal: Principal = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    if user_id == principal.id:
        raise HTTPException(400, "不能停用自己的账号")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "user not found")
    if user.role == "superadmin":
        raise HTTPException(400, "不能停用超管账号")
    before = user.status
    user.status = body.status
    _audit(db, principal, "status_change", user_id, {"from": before, "to": body.status}, request)
    db.commit()
    return {"ok": True, "id": user_id, "status": user.status}


# 获取用户用量
@router.get("/usage")
def usage(
    day: str | None = None,
    _admin: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(UsageDaily)
    if day:
        q = q.filter(UsageDaily.day == day)
    rows = q.all()
    return [
        {
            "user_id": r.user_id,
            "day": r.day,
            "messages": r.messages,
            "tokens_in": r.tokens_in,
            "tokens_out": r.tokens_out,
            "tool_calls": r.tool_calls,
            "cost": r.cost,
        }
        for r in rows
    ]


# 获取 run 详情
@router.get("/runs/{run_id}")
def run_detail(
    run_id: str,
    _admin: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "run not found")
    messages = db.query(Message).filter(Message.run_id == run_id).order_by(Message.created_at).all()
    tools = db.query(ToolCall).filter(ToolCall.run_id == run_id).order_by(ToolCall.created_at).all()
    return {
        "run": {
            "id": run.id,
            "status": run.status,
            "tokens_in": run.tokens_in,
            "tokens_out": run.tokens_out,
            "cost": run.cost,
            "error": run.error,
        },
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "tool_calls": [
            {
                "tool": t.tool_name,
                "args": t.args_json,
                "result": t.result_summary,
                "status": t.status,
                "elapsed_ms": t.elapsed_ms,
            }
            for t in tools
        ],
    }


# 获取存储使用情况
@router.get("/storage")
def storage(_admin: Principal = Depends(require_admin)):
    total = 0
    per_dir: dict[str, int] = {}
    for root, _dirs, files in os.walk(settings.data_dir):
        for name in files:
            path = os.path.join(root, name)
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            total += size
            rel = os.path.relpath(root, settings.data_dir).split(os.sep)[0]
            per_dir[rel] = per_dir.get(rel, 0) + size
    return {
        "total_mb": round(total / 1024 / 1024, 2),
        "dirs_mb": {k: round(v / 1024 / 1024, 2) for k, v in per_dir.items()},
    }