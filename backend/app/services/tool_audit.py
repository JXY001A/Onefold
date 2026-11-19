"""工具调用审计：往 tool_calls 表写一行。

与 messages 表分工：这里只存「可统计的摘要」（参数、耗时、成败、结果前 200 字），
网页正文只进 messages，避免同一份几 KB 的内容存两遍。
"""

import json
from uuid import uuid4

from ..db import SessionLocal
from ..models import ToolCall, now

SUMMARY_MAX = 200
# 结构化结果整体上限：几十条搜索结果也存得下，又能挡住异常的大对象
DATA_MAX = 200_000


def save_tool_call(
    run_id: str,
    tool_name: str,
    args: str,
    summary: str,
    status: str,
    elapsed_ms: int,
    llm_call_id: str | None = None,
    step: int = 0,
    error: str | None = None,
    data: dict | None = None,
) -> None:
    """写一条审计记录。失败也不该影响对话，所以吞掉异常由调用方记日志。"""
    db = SessionLocal()
    try:
        db.add(
            ToolCall(
                id=str(uuid4()),
                run_id=run_id,
                tool_name=tool_name[:64],
                args_json=args,
                result_summary=(summary or "")[:SUMMARY_MAX],
                data_json=json.dumps(data, ensure_ascii=False)[:DATA_MAX] if data else None,
                status=status,
                elapsed_ms=elapsed_ms,
                llm_call_id=llm_call_id,
                step=step,
                error=error,
                created_at=now(),
            )
        )
        db.commit()
    finally:
        db.close()
