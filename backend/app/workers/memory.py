"""长期记忆 worker：轮询 memory_jobs，调 DeepSeek 提取，写 memory_items。

独立进程运行：
    python -m app.workers.memory
不接收 HTTP，不与 Web 进程共享内存；所有协调都通过 PostgreSQL。
"""

from __future__ import annotations

import json
import logging
import signal
import threading
import time
from datetime import datetime
from typing import Any, Literal

from openai import OpenAI
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from ..config import settings
from ..db import SessionLocal, init_db
from ..models import MemoryItem
from ..services.memory import (
    apply_extraction,
    claim_memory_job,
    fail_memory_job,
    finish_memory_job,
    memory_enabled_for,
    requeue_stale_jobs,
    run_turns,
)

logger = logging.getLogger("onefold.memory_worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class CardOp(BaseModel):
    """模型返回的一张卡片；只接受 upsert，不在这里做删除。

    category  身份/偏好/项目/约束/关系/其他
    key       卡片的稳定标识（如 name、tech_stack），同一 key 视为同一事实
    value     结构化值（JSON 可表达的任意类型），null 不合法
    text      给人看的一句话描述，限制长度避免占满上下文
    """

    action: Literal["upsert"] = "upsert"
    category: str = Field(min_length=1, max_length=32)
    key: str = Field(min_length=1, max_length=64)
    value: Any
    text: str = Field(min_length=1, max_length=settings.memory_card_chars)
    confidence: float = Field(default=0.8, ge=0, le=1)
    source_message_id: str

    @field_validator("value")
    @classmethod
    def value_not_null(cls, value: Any) -> Any:
        # 卡片必须有值；null 卡片没有注入意义
        if value is None:
            raise ValueError("card value must not be null")
        return value


class NoteOp(BaseModel):
    """模型返回的一条笔记；text 必须是短背景，不是整段对话。

    happened_at 可选，用来保留「什么时候发生」这类时间信息。
    """

    action: Literal["add"] = "add"
    category: str = Field(default="other", max_length=32)
    text: str = Field(min_length=1, max_length=settings.memory_note_chars)
    confidence: float = Field(default=0.8, ge=0, le=1)
    happened_at: datetime | None = None
    source_message_id: str


class ExtractionResult(BaseModel):
    """一次提取的完整结果，对应模型返回的 {"cards": [...], "notes": [...]}。"""

    cards: list[CardOp] = Field(default_factory=list)
    notes: list[NoteOp] = Field(default_factory=list)


SYSTEM_PROMPT = """你是用户长期记忆提取器。只提取用户明确说过或明确确认过的信息。

规则：
1. 用户的话是主要证据；助手的话只用于理解上下文，不能单独成为用户事实。
2. 不保存搜索结果、工具输出、临时任务进度、模型推测。
3. 稳定事实/偏好写 card；带原因、时间、人物、事件的写 note。
4. 每条记忆必须给出 source_message_id，且必须是上下文中 role=user 的消息。
5. 没有值得长期保留的信息时，返回 {"cards": [], "notes": []}；不要凑数。
6. 候选信息已存在于当前卡片时，也返回空数组，不要重复写入。
7. 不保存密码、API Key、身份证号、银行卡号等敏感信息。
8. 只输出 JSON，不要输出解释。"""


def _existing_cards(owner_key: str) -> list[dict[str, Any]]:
    """给模型看当前卡片，便于判断重复/更新。

    只取 status=active 的卡片，已软删除的不再送给模型；
    返回精简字段（不含 id / 计数），减少 prompt 体积。
    """
    db = SessionLocal()
    try:
        rows = db.execute(
            select(MemoryItem).where(
                MemoryItem.owner_key == owner_key,
                MemoryItem.kind == "card",
                MemoryItem.status == "active",
            )
        ).scalars().all()
        return [
            {"category": r.category, "key": r.key, "value": r.value, "text": r.text}
            for r in rows
        ]
    finally:
        db.close()


def _build_messages(owner_key: str, turns: list[dict[str, str]], priority: int) -> list[dict]:
    """把最近对话和已有卡片拼成提取 prompt；显式记住会加一句强约束。

    每条对话前缀标上 [message_id] 和角色，模型必须原样引用这个 id 作为证据，
    后面的 process_job 会拿它去校验（只接受 role=user 的 id）。
    """
    # 拿到传入用户的现有卡片
    cards = _existing_cards(owner_key)
    conversation = "\n".join(
        f"[{t['id']}] {t['role'].upper()}: {t['content']}" for t in turns
    )
    user_note = (
        "\n用户明确要求记住这次内容，请优先提取；仍必须遵守证据规则。"
        if priority >= 10
        else ""
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT + user_note},
        {
            "role": "user",
            "content": (
                f"当前卡片：\n{json.dumps(cards, ensure_ascii=False, default=str)}\n\n"
                f"最近对话：\n{conversation}\n\n"
                "请输出 JSON：{\"cards\": [...], \"notes\": [...]}"
            ),
        },
    ]


def _extract(owner_key: str, turns: list[dict[str, str]], priority: int) -> ExtractionResult:
    """同步调用 DeepSeek；worker 是独立进程，阻塞这里不影响 Web。"""
    if not settings.api_key:
        raise RuntimeError("API_KEY is not set")

    # 复用一个 client 实例即可；60s 超时防止网络抖动把 worker 线程挂死
    client = OpenAI(api_key=settings.api_key, base_url=settings.base_url, timeout=60)
    response = client.chat.completions.create(
        model=settings.model,
        messages=_build_messages(owner_key, turns, priority),
        # 提取任务需要稳定输出，温度压低到配置值
        temperature=settings.memory_prompt_temperature,
        # 强制 JSON 模式，避免模型输出解释文字导致解析失败
        response_format={"type": "json_object"},
    )
    content = (response.choices[0].message.content or "{}").strip()
    # 有些兼容端点会把 JSON 包在 ```json 围栏里，先剥掉再解析
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
    # 用 Pydantic 解析并校验：{} 里的 cards/notes 会被转成 CardOp/NoteOp，
    # 字段缺失或类型不符直接抛 ValidationError，由 worker_loop 捕获后走失败重试
    return ExtractionResult.model_validate_json(content)


def process_job(job: dict[str, Any]) -> None:
    """处理一条 job；空结果、重复、成功、失败分别落到不同 result。

    skipped：开关已关闭 / 没有用户发言
    empty：模型没提取出有价值的记忆
    written：有新写入或更新
    no_change：只是强化计数或命中重复，数据没实质变化
    """
    owner_key = job["owner_key"]
    # 该用户记忆开关是否被关闭
    if not memory_enabled_for(owner_key):
        finish_memory_job(job["id"], "skipped", {"reason": "memory_disabled"})
        return

    # 获取当前会话前面的 memory_max_turns 轮会话
    turns = run_turns(job["run_id"], settings.memory_max_turns)
    user_turns = [t for t in turns if t["role"] == "user"]
    if not user_turns:
        finish_memory_job(job["id"], "skipped", {"reason": "no_turns"})
        return

    # 白名单：只有用户本人说过的话才能作为证据
    allowed_ids = {t["id"] for t in user_turns}
    
    # 调用模型提取记忆
    result = _extract(owner_key, turns, int(job.get("priority") or 0))

    # 只保留有用户证据的候选；模型编造或引用了助手/工具消息的 message id 直接丢弃
    cards = [
        c.model_dump()
        for c in result.cards[: settings.memory_extract_max_cards]
        if c.source_message_id in allowed_ids
    ]
    notes = [
        n.model_dump()
        for n in result.notes[: settings.memory_extract_max_notes]
        if n.source_message_id in allowed_ids
    ]

    if not cards and not notes:
        finish_memory_job(job["id"], "empty", {"cards": 0, "notes": 0})
        return

    # 落库：新增/更新卡片、写入笔记、重复则强化 mention_count
    stats = apply_extraction(owner_key, job["run_id"], cards, notes)
    # 有实质写入才算 written，否则降级为 no_change / empty，便于统计口径区分
    if stats.get("added", 0) or stats.get("updated", 0) or stats.get("notes", 0):
        result_name = "written"
    elif stats.get("reinforced", 0) or stats.get("duplicates", 0):
        result_name = "no_change"
    else:
        result_name = "empty"
    finish_memory_job(job["id"], result_name, stats)

# 参数都在线程启动的时候传入的
def worker_loop(worker_id: str, stop_event: threading.Event) -> None:
    """单个 worker 线程：抢任务 → 处理 → 没任务睡一会。"""
    # 没有收到程序终止信号，继续循环
    while not stop_event.is_set():
        # 抢任务
        job = claim_memory_job(worker_id)
        if job is None:
            # 没任务就 sleep 一下，避免 CPU 占用过高
            stop_event.wait(settings.memory_poll_s)
            continue
        # 处理任务
        try:
            process_job(job)
        # 处理失败就重试
        except Exception as exc:  # noqa: BLE001
            logger.exception("memory job %s failed", job.get("id"))
            fail_memory_job(job["id"], f"{type(exc).__name__}: {exc}", int(job.get("attempts") or 1))


def main() -> None:
    """启动固定数量的 worker 线程；SIGTERM 时停止抢新任务。"""
    # 建表兜底（首次部署或新增表时生效；不会改已有列结构）
    init_db()
    # 进程刚启动时把上次崩溃遗留在 running 状态的任务重新放回队列
    stale = requeue_stale_jobs()
    if stale:
        logger.warning("requeued %s stale memory jobs", stale)
    # 停止信号：所有线程都在等它，置位后各线程在下一次循环退出
    stop_event = threading.Event()

    def _stop(*_args) -> None:
        logger.info("memory worker shutting down")
        # 置位 stop_event 通知所有线程退出
        stop_event.set()

    # 捕获停止信号：正常退出时置位 stop_event
    signal.signal(signal.SIGTERM, _stop)
    # 捕获 Ctrl+C 退出时也置位 stop_event
    signal.signal(signal.SIGINT, _stop)

    # daemon=True：主线程退出时不阻塞进程结束
    threads = [
        # 创建 worker 线程
        threading.Thread(
            target=worker_loop,
            args=(f"memory-worker-{i + 1}", stop_event),
            daemon=True,
            name=f"memory-worker-{i + 1}",
        )
        for i in range(max(1, settings.memory_worker_concurrency))
    ]
    for thread in threads:
        thread.start()
    logger.info("memory worker started: %s threads", len(threads))

    # 主线程只做守护：每秒检查一次停止信号
    try:
        while not stop_event.is_set():
            time.sleep(1)
    finally:
        # 给在途任务 30s 收尾时间，超时则随进程一起退出
        for thread in threads:
            thread.join(timeout=30)


if __name__ == "__main__":
    main()
