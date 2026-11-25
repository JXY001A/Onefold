"""调用模型做一次记忆提取，并在 schema 不合法时自动修复一次。"""

import json
from typing import Any

from openai import OpenAI
from pydantic import ValidationError
from sqlalchemy import select

from ..config import settings
from ..db import SessionLocal
from ..models import MemoryItem
from .memory_schema import (
    EXTRACTION_EXAMPLE,
    EXTRACTION_SCHEMA,
    SYSTEM_PROMPT,
    ExtractionResult,
    MemorySchemaError,
)


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
    schema_rules = (
        "\n\n输出必须严格符合以下 JSON Schema：\n"
        + EXTRACTION_SCHEMA
        + "\n\n禁止使用 id、type、content 等未定义字段。"
        "card 必须有 category、key、value、text、source_message_id；"
        "note 必须有 text、source_message_id。"
        "\n示例：\n"
        + EXTRACTION_EXAMPLE
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT + user_note + schema_rules},
        {
            "role": "user",
            "content": (
                f"当前卡片：\n{json.dumps(cards, ensure_ascii=False, default=str)}\n\n"
                f"最近对话：\n{conversation}\n\n"
                "请输出 JSON：{\"cards\": [...], \"notes\": [...]}"
            ),
        },
    ]


def _call_model(client: OpenAI, messages: list[dict], temperature: float) -> str:
    """调一次 DeepSeek，返回原始 JSON 字符串。"""
    response = client.chat.completions.create(
        model=settings.model,
        messages=messages,
        temperature=temperature,
        # JSON mode 只保证“语法合法”，字段仍由 prompt + Pydantic 约束
        response_format={"type": "json_object"},
    )
    return (response.choices[0].message.content or "{}").strip()


def _parse_result(content: str) -> ExtractionResult:
    """剥掉可能的 ```json 围栏，再做严格字段校验。"""
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
    return ExtractionResult.model_validate_json(content)


def extract(owner_key: str, turns: list[dict[str, str]], priority: int) -> ExtractionResult:
    """同步调用 DeepSeek；失败时带着错误信息修复一次。"""
    if not settings.api_key:
        raise RuntimeError("API_KEY is not set")

    client = OpenAI(api_key=settings.api_key, base_url=settings.base_url, timeout=60)
    messages = _build_messages(owner_key, turns, priority)
    content = _call_model(client, messages, settings.memory_prompt_temperature)

    try:
        return _parse_result(content)
    except ValidationError as first_error:
        # 把模型自己的输出和 Pydantic 错误回给它，要求只修 JSON；
        # 修复后仍失败说明不是偶发漂移，直接交给 worker 标记 invalid_schema。
        errors = json.dumps(first_error.errors(), ensure_ascii=False, default=str)
        repair_messages = messages + [
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": (
                    "上一次输出不符合 schema，错误如下：\n"
                    f"{errors}\n\n"
                    "请只输出修正后的 JSON，不要解释；"
                    "字段必须严格使用 schema 中定义的 category/key/value/text/"
                    "source_message_id 等名称。"
                ),
            },
        ]
        try:
            repaired = _call_model(client, repair_messages, 0.0)
            return _parse_result(repaired)
        except ValidationError as second_error:
            raise MemorySchemaError(
                f"schema invalid after repair: {second_error}"
            ) from second_error