"""提取证据：只把用户与助手说过的话交给提取器，工具输出不算事实。"""

from sqlalchemy import select

from ..db import SessionLocal
from ..models import Message, Run


def run_turns(run_id: str, max_turns: int = 10) -> list[dict[str, str]]:
    """读取截至当前 run 的最近对话，只保留 user / assistant。

    用 started_at <= 当前 run 定位，保证能拿到跨多个 run 的上下文；
    tool 角色的消息不参与提取（工具输出不能当作事实）。
    """
    db = SessionLocal()
    try:
        current = db.get(Run, run_id)
        if current is None or current.started_at is None:
            return []
        runs = db.execute(
            select(Run)
            .where(
                Run.conversation_id == current.conversation_id,
                Run.started_at <= current.started_at,
            )
            .order_by(Run.started_at.desc())
            .limit(max_turns)
        ).scalars().all()
        run_ids = [r.id for r in runs]
        if not run_ids:
            return []
        rows = db.execute(
            select(Message)
            # 使用 in 逻辑找到有效的 message
            .where(Message.run_id.in_(run_ids), Message.role.in_(("user", "assistant")))
            .order_by(Message.created_at, Message.seq)
        ).scalars().all()
        return [
            {"id": m.id, "run_id": m.run_id, "role": m.role, "content": m.content}
            for m in rows
        ]
    finally:
        db.close()


def message_is_user_evidence(run_id: str, message_id: str) -> bool:
    """防止模型把助手的话/搜索结果当作用户事实。"""
    db = SessionLocal()
    try:
        row = db.scalar(
            select(Message).where(
                Message.id == message_id,
                Message.run_id == run_id,
                Message.role == "user",
            )
        )
        return row is not None
    finally:
        db.close()