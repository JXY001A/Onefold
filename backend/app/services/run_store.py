"""轮次与消息落库：每轮 run 的生命周期，以及一轮消息的批量写入。

messages 表只有 run_id，所以「按会话查消息」要借道 runs，见 message_reader。
"""

import json
from uuid import uuid4

from sqlalchemy import func, select

from ..db import SessionLocal
from ..models import Message, Run, now


def save_transcript(run_id: str, messages: list[dict]) -> None:
    """把一轮的完整消息落库（含工具步骤），seq 从 1 递增。

    messages 用 OpenAI 形状；assistant 的 tool_calls 存 JSON，tool 行通过
    tool_call_id 与它配对 —— 这是下一轮能原样回放的前提。
    """
    db = SessionLocal()
    try:
        for seq, m in enumerate(messages, 1):
            role = m.get("role")
            if role not in ("user", "assistant", "tool"):
                continue
            calls = m.get("tool_calls")
            db.add(
                Message(
                    id=str(uuid4()),
                    run_id=run_id,
                    role=role,
                    content=m.get("content") or "",
                    seq=seq,
                    tool_call_id=m.get("tool_call_id"),
                    tool_name=m.get("name"),
                    tool_calls_json=json.dumps(calls, ensure_ascii=False) if calls else None,
                    created_at=now(),
                )
            )
        db.commit()
    finally:
        db.close()


def create_run(user_id: str | None, conversation_id: str | None) -> str:
    """开始一轮对话：先建 run 记录，后续消息都挂在这个 run 下。返回 run_id。"""
    run_id = str(uuid4())
    db = SessionLocal()
    try:
        # 会话内轮次号：UUID 不适合做范围查询，turn_no 才是稳定排序依据
        last_turn = (
            db.scalar(
                select(func.max(Run.turn_no)).where(
                    Run.conversation_id == conversation_id
                )
            )
            if conversation_id
            else 0
        )
        db.add(
            Run(
                id=run_id,
                user_id=user_id,
                conversation_id=conversation_id,
                turn_no=int(last_turn or 0) + 1,
                status="running",
                started_at=now(),
            )
        )
        db.commit()
    finally:
        db.close()
    return run_id


def finish_run(run_id: str, status: str = "done", error: str | None = None) -> None:
    """结束一轮对话：更新 run 状态与结束时间。status: done / cancelled / error。"""
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        if run:
            run.status = status
            run.ended_at = now()
            run.error = error
            db.commit()
    finally:
        db.close()