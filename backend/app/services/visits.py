"""访问记录读写。

一条 visits 记录 = 一次「打开站点 → 停留 → 离开」：
    进入   POST /api/visits/enter            → 建记录，返回 visit_id
    心跳   POST /api/visits/{id}/heartbeat   → 刷新 last_active_at（判断「还在看」）
    离开   POST /api/visits/{id}/leave       → 写入 left_at 与停留时长

服务端能拿到的（IP、UA）在这里采集；屏幕、语言、时区、来源页只有浏览器知道，
由前端在 enter 时上报。离开事件可能丢失（关进程、断网），所以 last_active_at
是比 left_at 更可靠的「最后一次活动时间」。
"""

from uuid import uuid4

from fastapi import Request

from ..db import SessionLocal
from ..models import Visit, as_utc, now
from .ua import parse_ua


def _clean_ip(ip: str | None) -> str | None:
    """去掉 IPv6 映射前缀（::ffff:127.0.0.1 → 127.0.0.1），便于后续按 IP 聚合。"""
    if not ip:
        return None
    return ip[7:] if ip.startswith("::ffff:") else ip


def _cut(value: str | None, size: int) -> str | None:
    """入库前按列宽截断，避免超长上报导致写入失败。"""
    if not value:
        return None
    return value[:size]


def record_visit(principal, request: Request, client: dict) -> dict:
    """记录一次进入：服务端信息 + 前端上报信息合并入库。"""
    ua = request.headers.get("user-agent") or ""
    info = parse_ua(ua)
    entered = now()

    db = SessionLocal()
    try:
        visit = Visit(
            id=str(uuid4()),
            owner_key=principal.owner_key,
            kind=principal.kind,
            ip=_clean_ip(request.client.host if request.client else None),
            user_agent=_cut(ua, 255),
            device=info["device"],
            os=info["os"],
            browser=info["browser"],
            screen=_cut(client.get("screen"), 16),
            language=_cut(client.get("language"), 32),
            timezone=_cut(client.get("timezone"), 64),
            referrer=_cut(client.get("referrer"), 255),
            entry_path=_cut(client.get("path"), 255),
            entered_at=entered,
            last_active_at=entered,
        )
        db.add(visit)
        db.commit()
        return {"visit_id": visit.id, "entered_at": entered.isoformat()}
    finally:
        db.close()


def touch_visit(visit_id: str, owner_key: str) -> bool:
    """刷新活跃时间。不是自己的记录一律返回 False（不区分「不存在」与「无权」）。"""
    db = SessionLocal()
    try:
        visit = db.get(Visit, visit_id)
        if visit is None or visit.owner_key != owner_key:
            return False
        visit.last_active_at = now()
        db.commit()
        return True
    finally:
        db.close()


def end_visit(visit_id: str, owner_key: str) -> bool:
    """记录离开时间与停留时长。重复上报（如 bfcache 恢复后再离开）不覆盖首次结果。"""
    db = SessionLocal()
    try:
        visit = db.get(Visit, visit_id)
        if visit is None or visit.owner_key != owner_key:
            return False
        if visit.left_at is None:
            left = now()
            visit.left_at = left
            visit.last_active_at = left
            visit.duration_s = int((left - as_utc(visit.entered_at)).total_seconds())
            db.commit()
        return True
    finally:
        db.close()