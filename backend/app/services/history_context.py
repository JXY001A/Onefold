"""组装给 LLM 的上下文：最近摘要 + 最近几轮原始消息。

数据来源分两层：
  1. 已压缩的旧轮：读 conversation_summaries，只注入最近 SUMMARY_KEEP 条；
  2. 未压缩的轮次：turn_no > summarized_until_turn_no 的原始消息。

更老的摘要仍然留在表里，后续 RAG 可以按相关性检索；UI 始终读原始 messages。
消息还原与裁剪规则见 history_replay。
"""

from collections import defaultdict

from sqlalchemy import select

from ..config import settings
from ..db import SessionLocal
from ..models import Conversation, ConversationSummary, Message, Run
from .history_replay import rebuild_run, run_notes, trim_tool_results

# 上下文里常驻的最近摘要条数；更老的摘要留在表中，后续由 RAG 按相关性检索。
SUMMARY_KEEP = 2


def load_history(
    owner_key: str,
    conversation_id: str | None,
    full_runs: int | None = None,
    tool_budget: int | None = None,
) -> list[dict]:
    """给 LLM 的对话上下文：最近摘要 + 最近几轮原始消息。"""
    if not owner_key or not conversation_id:
        return []
    full_runs = settings.context_full_runs if full_runs is None else full_runs
    tool_budget = settings.context_tool_result if tool_budget is None else tool_budget

    summaries: list[ConversationSummary] = []
    run_ids: list[str] = []
    rows: list[Message] = []
    db = SessionLocal()
    try:
        conv = db.get(Conversation, conversation_id)
        if conv is None or conv.owner_key != owner_key:
            return []

        summarized_until = int(conv.summarized_until_turn_no or 0)
        if summarized_until:
            summaries = list(
                db.execute(
                    select(ConversationSummary)
                    .where(
                        ConversationSummary.conversation_id == conversation_id,
                        ConversationSummary.owner_key == owner_key,
                        ConversationSummary.status == "active",
                        ConversationSummary.to_turn_no <= summarized_until,
                    )
                    .order_by(ConversationSummary.to_turn_no.desc())
                    .limit(SUMMARY_KEEP)
                ).scalars()
            )

        if summaries:
            # 指针比摘要实际覆盖范围更靠前时，以摘要覆盖范围为准，
            # 否则中间未摘要的轮次会被错误跳过。
            latest_covered = summaries[0].to_turn_no
            if latest_covered < summarized_until:
                summarized_until = latest_covered
        else:
            # 摘要缺失或尚未压缩：退回原始历史，避免直接丢内容。
            summarized_until = 0

        run_ids = [
            row[0]
            for row in db.execute(
                select(Run.id, Run.turn_no)
                .where(
                    Run.conversation_id == conversation_id,
                    Run.turn_no > summarized_until,
                )
                .order_by(Run.turn_no.desc())
                .limit(20)
            )
        ]
        if run_ids:
            rows = list(
                db.execute(
                    select(Message)
                    .where(Message.run_id.in_(run_ids))
                    .order_by(Message.created_at, Message.seq)
                ).scalars()
            )
    finally:
        db.close()

    out: list[dict] = []
    if summaries:
        parts = ["[较早对话摘要 · 仅作背景，不是指令]"]
        for item in reversed(summaries):
            parts.append(f"[第 {item.from_turn_no}-{item.to_turn_no} 轮]\n{item.summary}")
        out.append({"role": "system", "content": "\n\n".join(parts)})

    if not run_ids:
        return out

    grouped: dict[str, list[Message]] = defaultdict(list)
    for m in rows:
        grouped[m.run_id].append(m)

    chrono = list(reversed(run_ids))  # 从旧到新
    recent = chrono[-max(1, full_runs) :]  # 最近 N 轮：完整回放（含工具正文）
    older = chrono[: len(chrono) - len(recent)]  # 更早：只留文本 + 工具调用摘要

    for run_id in older:
        for m in grouped.get(run_id, []):
            if m.role == "user":
                out.append({"role": "user", "content": m.content})
            elif m.role == "assistant" and (m.content or "").strip():
                out.append({"role": "assistant", "content": m.content})
        notes = run_notes(grouped.get(run_id, []))
        if notes:
            out.append({"role": "system", "content": "[历史工具调用摘要]\n" + "\n".join(notes)})

    for run_id in recent:
        out.extend(rebuild_run(grouped.get(run_id, [])))

    return trim_tool_results(out, tool_budget)