"""历史压缩：判断能不能压、调模型生成摘要、推进压缩指针。

触发时机是一轮对话结束后（由 chat 接口异步调度），失败只记日志，
绝不影响聊天本身；并发下靠行锁 + 指针比对保证只有一次写入成功。
"""

import asyncio
import logging
from collections import defaultdict
from typing import Awaitable, Callable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..config import settings
from ..db import SessionLocal
from ..models import Conversation, ConversationSummary, Message, Run, now
from .history_summary import (
    SUMMARY_PROMPT_VERSION,
    SUMMARY_SYSTEM_PROMPT,
    estimate_tokens,
    format_runs_for_summary,
)
from .llm import chat

logger = logging.getLogger(__name__)

# 保存后台任务引用，避免 asyncio 任务被 GC；完成后自动移除。
_COMPACTION_TASKS: set[asyncio.Task] = set()


def schedule_compaction(conversation_id: str, owner_key: str) -> None:
    """本轮结束后异步压缩旧历史，不阻塞 SSE 响应。"""
    try:
        task = asyncio.create_task(maybe_compact_history(conversation_id, owner_key))
        _COMPACTION_TASKS.add(task)
        # add_done_callback：任务完成后从集合里移除，避免内存泄漏
        task.add_done_callback(_COMPACTION_TASKS.discard)
    except RuntimeError:
        logger.exception("schedule history compaction failed: %s", conversation_id)


def _prepare_compaction(conversation_id: str, owner_key: str) -> dict | None:
    """选出可以压缩的旧轮次；不满足阈值或没有旧轮时返回 None。"""
    keep_raw = max(1, settings.history_raw_runs)
    db = SessionLocal()
    try:
        conv = db.get(Conversation, conversation_id)
        if conv is None or conv.owner_key != owner_key:
            return None

        current_until = int(conv.summarized_until_turn_no or 0)
        # 多取一条：最后一条就是“保留区”之前最靠后的 turn_no，作为本批截止点。
        recent_turns = list(
            db.execute(
                select(Run.turn_no)
                .where(Run.conversation_id == conversation_id)
                .order_by(Run.turn_no.desc())
                .limit(keep_raw + 1)
            ).scalars()
        )
        if len(recent_turns) <= keep_raw:
            return None

        cutoff = int(recent_turns[-1])
        if cutoff <= current_until:
            return None

        runs = list(
            db.execute(
                select(Run)
                .where(
                    Run.conversation_id == conversation_id,
                    Run.turn_no > current_until,
                    Run.turn_no <= cutoff,
                )
                .order_by(Run.turn_no)
            ).scalars()
        )
        if not runs:
            return None

        rows = list(
            db.execute(
                select(Message)
                .where(Message.run_id.in_([r.id for r in runs]))
                .order_by(Message.created_at, Message.seq)
            ).scalars()
        )
        grouped: dict[str, list[Message]] = defaultdict(list)
        for m in rows:
            grouped[m.run_id].append(m)

        source_text = format_runs_for_summary(runs, grouped)
        source_tokens = estimate_tokens(source_text)
        if source_tokens <= settings.history_compact_tokens:
            return None

        return {
            "conversation_id": conversation_id,
            "owner_key": owner_key,
            "current_until": current_until,
            "from_turn_no": runs[0].turn_no,
            "to_turn_no": runs[-1].turn_no,
            "from_run_id": runs[0].id,
            "to_run_id": runs[-1].id,
            "source_text": source_text,
            "source_tokens": source_tokens,
        }
    finally:
        db.close()


def _save_compaction(plan: dict) -> bool:
    """写入摘要并推进指针；并发下只允许一个任务成功。"""
    db = SessionLocal()
    try:
        conv = db.execute(
            select(Conversation)
            .where(Conversation.id == plan["conversation_id"])
            # 拿到锁：其他事务不能同时修改该会话
            .with_for_update()
        ).scalar_one_or_none()
        if conv is None or conv.owner_key != plan["owner_key"]:
            return False
        if int(conv.summarized_until_turn_no or 0) != plan["current_until"]:
            return False

        db.add(
            ConversationSummary(
                id=str(uuid4()),
                conversation_id=plan["conversation_id"],
                owner_key=plan["owner_key"],
                from_turn_no=plan["from_turn_no"],
                to_turn_no=plan["to_turn_no"],
                from_run_id=plan["from_run_id"],
                to_run_id=plan["to_run_id"],
                summary=plan["summary"],
                summary_tokens=plan["summary_tokens"],
                source_tokens=plan["source_tokens"],
                model=settings.model,
                prompt_version=SUMMARY_PROMPT_VERSION,
                status="active",
                created_at=now(),
            )
        )
        conv.summarized_until_turn_no = plan["to_turn_no"]
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        logger.info("history summary already exists: %s", plan["conversation_id"])
        return False
    finally:
        db.close()


async def _summarize_source(source_text: str) -> str:
    response = await chat(
        [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": "请压缩以下对话历史：\n\n" + source_text},
        ],
        max_tokens=settings.history_summary_max_tokens,
        # 要求模型输出尽可能稳定的摘要，降低发散性
        temperature=0.2,
    )
    if not response.choices:
        return ""
    return (response.choices[0].message.content or "").strip()


async def maybe_compact_history(
    conversation_id: str,
    owner_key: str,
    summarizer: Callable[[str], Awaitable[str]] | None = None,
) -> bool:
    """一轮结束后尝试压缩旧历史；失败只记日志，不影响聊天。"""
    try:
        # 拿到符合要求的会话轮次文本内容
        plan = _prepare_compaction(conversation_id, owner_key)
        if plan is None:
            return False

        summary = await (summarizer or _summarize_source)(plan["source_text"])
        summary = (summary or "").strip()
        if not summary:
            logger.warning("history summary empty: %s", conversation_id)
            return False

        plan["summary"] = summary
        plan["summary_tokens"] = estimate_tokens(summary)
        return _save_compaction(plan)
    except Exception:
        logger.exception("history compaction failed: %s", conversation_id)
        return False