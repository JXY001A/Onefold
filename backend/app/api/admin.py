"""管理后台（骨架）：审批、用户、用量、run 详情、存储。"""

import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import AccessRequest, Message, Run, ToolCall, UsageDaily, User

# 使用 router 将权限相关接口统一到 /api/admin 路由下
router = APIRouter()

# 获取访问请求列表
@router.get("/requests")
def list_requests(db: Session = Depends(get_db)):
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
def approve_request(request_id: str, db: Session = Depends(get_db)):
    req = db.get(AccessRequest, request_id)
    if not req:
        raise HTTPException(404, "request not found")
    req.status = "approved"
    req.code = f"OF-{uuid4().hex[:8].upper()}"
    req.decided_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "code": req.code}

# 获取用户列表
@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    rows = db.query(User).all()
    return [
        {"id": u.id, "username": u.username, "role": u.role, "status": u.status}
        for u in rows
    ]

# 获取用户用量
@router.get("/usage")
def usage(day: str | None = None, db: Session = Depends(get_db)):
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
def run_detail(run_id: str, db: Session = Depends(get_db)):
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
def storage():
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
