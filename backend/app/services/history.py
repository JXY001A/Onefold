"""会话存取：会话元信息（conversations）、历史消息（messages）与每轮执行（runs）。

数据层级：
    conversations（会话：标题 / 归属 / 活跃时间）
        └── runs（每轮执行：状态 / 耗时 / token）
                └── messages（消息：角色 / 内容）

归属统一用 owner_key（格式与 Principal.lock_key 一致）：
    user:<user_id>    登录用户
    guest:<guest_id>  匿名访客
两种身份走同一套规则，访客因此也能拥有多个会话。

注意：messages 表只有 run_id，所以「按会话查消息」必须借道 runs：
    messages.run_id → runs.id，再由 runs.conversation_id 过滤。
"""

from collections import defaultdict
from datetime import timedelta
import html
import json
import re
from uuid import uuid4

from sqlalchemy import func, select

from ..config import settings
from ..db import SessionLocal
from ..models import Conversation, Message, Run, ToolCall, now

# 标题取首条用户消息的前 N 个字
TITLE_MAX = 30


def _make_title(text: str | None) -> str | None:
    """把首条消息压成一行标题（压缩空白 + 超长截断）。"""
    if not text:
        return None
    title = " ".join(text.split())
    if not title:
        return None
    return title[:TITLE_MAX] + ("…" if len(title) > TITLE_MAX else "")


def get_or_create_conversation(
    owner_key: str,
    conversation_id: str | None = None,
    title_seed: str | None = None,
) -> str:
    """定位或新建会话，并刷新活跃时间（列表按它排序），返回 conversation_id。

    - 传入 conversation_id：必须存在且属于 owner_key，否则抛 PermissionError；
    - 不传：新建会话，标题取首条用户消息。
    """
    db = SessionLocal()
    try:
        if conversation_id:
            conv = db.get(Conversation, conversation_id)
            if conv is None or conv.owner_key != owner_key:
                raise PermissionError(conversation_id)
            conv.updated_at = now()
            # 早期建的空标题会话，等首条消息补上
            if not conv.title:
                conv.title = _make_title(title_seed)
            db.commit()
            return conv.id

        conv = Conversation(
            id=str(uuid4()),
            owner_key=owner_key,
            title=_make_title(title_seed),
            created_at=now(),
            updated_at=now(),
        )
        db.add(conv)
        db.commit()
        return conv.id
    finally:
        db.close()


def conversation_owned_by(conversation_id: str, owner_key: str) -> bool:
    """会话是否属于该身份。登录用户与访客统一按 owner_key 判断。"""
    db = SessionLocal()
    try:
        conv = db.get(Conversation, conversation_id)
        return conv is not None and conv.owner_key == owner_key
    finally:
        db.close()


def list_conversations(owner_key: str, days: int = 20, limit: int = 100) -> list[dict]:
    """最近 days 天内有过活动的会话，按活跃时间倒序。"""
    since = now() - timedelta(days=days)
    db = SessionLocal()
    try:
        stmt = (
            select(Conversation)
            .where(
                Conversation.owner_key == owner_key,
                Conversation.updated_at >= since,
            )
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        rows = db.execute(stmt).scalars()
        return [
            {
                "conversation_id": c.id,
                "title": c.title or "新对话",
                "updated_at": c.updated_at.isoformat(),
            }
            for c in db.execute(stmt).scalars()
        ]
    finally:
        db.close()


# 老会话没有 data_json：从工具正文里还原标题与链接，否则侧栏只剩一段正文碎片（格式见 tools/web.py）
_HEAD = re.compile(r"^\[(\d+)\]\s*([^\n]+)")
_SOURCE = re.compile(r'<external_content source="([^"]*)"')
_FETCH_TITLE = re.compile(r"^标题：(.+)$", re.MULTILINE)
# 侧栏简介长度上限（与 tools/web.py 的 BRIEF_CHARS 保持一致）
SNIPPET_MAX = 120


def _plain(text: str) -> str:
    """正文压成一行：去掉行首 > / # 标记与页内层级符（与 tools/web.py 的 _clean 一致）。"""
    lines = [ln.strip().lstrip(">#").strip() for ln in text.splitlines()]
    return re.sub(r"\s*>\s*", " ", " ".join(" ".join(lines).split())).strip()


def _split_meta(head: str) -> tuple[str, str, str]:
    """「标题（站点 · 日期）」拆成三段；没有括号就整串当标题。"""
    m = re.match(r"(.+?)（(.+)）$", head)
    if not m:
        return head, "", ""
    parts = [x.strip() for x in m.group(2).split("·")]
    return m.group(1).strip(), parts[0], parts[1] if len(parts) > 1 else ""


def _parse_tool_text(text: str, name: str | None) -> dict | None:
    """从工具正文还原命中列表（老会话兜底，链接必须可点）。"""
    if not text:
        return None
    src = _SOURCE.search(text)
    url = html.unescape(src.group(1)) if src else ""
    if name == "fetch_url":
        if not url:
            return None
        m = _FETCH_TITLE.search(text)
        title = m.group(1).strip() if m else ""
        return {"kind": "fetch", "url": url, "title": title or url, "chars": len(_plain(text))}
    items = []
    for block in re.split(r"\n\n(?=\[\d+\])", text):
        head = _HEAD.match(block.strip())
        if not head:
            continue
        title, site, date = _split_meta(head.group(2).strip())
        hit = _SOURCE.search(block)
        rest = block[hit.end() :] if hit else ""
        items.append(
            {
                "title": title,
                "url": html.unescape(hit.group(1)) if hit else "",
                "site": site,
                "date": date,
                "snippet": _plain(rest)[:SNIPPET_MAX],
            }
        )
    return {"kind": "search", "items": items} if items else None


def load_conversation_messages(conversation_id: str, limit: int = 200) -> list[dict]:
    """按会话读取消息（含工具步骤），取最近 limit 条后转正序，供前端渲染历史。

    工具行的正文动辄几千字且以标签开头，只回审计表里的短文案
    （如「找到 5 条结果」）与成败，供前端画一行痕迹。
    归属校验由调用方先做（本函数只负责取数）。
    """
    db = SessionLocal()
    try:
        stmt = (
            select(Message, ToolCall.status, ToolCall.result_summary, ToolCall.data_json)
            .join(Run, Message.run_id == Run.id)
            # 审计行与消息行靠 (run_id, call_id) 对齐；审计写失败时为空，前端退化为只显示工具名
            .outerjoin(
                ToolCall,
                (ToolCall.run_id == Message.run_id)
                & (ToolCall.llm_call_id == Message.tool_call_id),
            )
            .where(Run.conversation_id == conversation_id)
            .order_by(Message.created_at.desc(), Message.seq.desc())
            .limit(limit)
        )
        rows = list(db.execute(stmt))
    finally:
        db.close()

    out: list[dict] = []
    for r, status, summary, data_json in reversed(rows):
        row: dict = {
            "role": r.role,
            "content": "" if r.role == "tool" else r.content,
            "created_at": r.created_at.isoformat(),
        }
        if r.role == "tool":
            row["tool_call_id"] = r.tool_call_id
            row["tool_name"] = r.tool_name
            row["summary"] = summary or ""
            row["tool_ok"] = None if status is None else status == "ok"
            # 结构化结果（搜索命中的标题/链接/简介），供前端侧栏展示
            try:
                row["tool_data"] = json.loads(data_json) if data_json else None
            except ValueError:
                row["tool_data"] = None
            if not row["tool_data"]:
                row["tool_data"] = _parse_tool_text(r.content or "", r.tool_name)
        elif r.tool_calls_json:
            # 库里存的是 OpenAI 原始结构，前端只需要 name/arguments
            row["tool_calls"] = [
                {
                    "id": c.get("id"),
                    "name": (c.get("function") or {}).get("name"),
                    "arguments": (c.get("function") or {}).get("arguments"),
                }
                for c in json.loads(r.tool_calls_json)
            ]
        out.append(row)
    return out


def load_history(
    owner_key: str,
    conversation_id: str | None,
    full_runs: int | None = None,
    tool_budget: int | None = None,
) -> list[dict]:
    """给 LLM 的对话上下文：最近几轮完整回放，更早的降级成文本 + 检索摘要。

    为什么按「轮」而不是按「条」裁剪：OpenAI 协议要求 tool 消息紧跟带
    tool_calls 的 assistant，按条截断会把这一组切开，上游会直接 400。

    返回的是 OpenAI 消息形状，可能包含：
        user / assistant（可带 tool_calls）/ tool / system（历史检索摘要）
    """
    if not owner_key or not conversation_id:
        return []
    full_runs = settings.context_full_runs if full_runs is None else full_runs
    tool_budget = settings.context_tool_result if tool_budget is None else tool_budget

    db = SessionLocal()
    try:
        run_ids = [
            row[0]
            for row in db.execute(
                select(Run.id)
                .join(Conversation, Conversation.id == Run.conversation_id)
                .where(
                    Run.conversation_id == conversation_id,
                    Conversation.owner_key == owner_key,
                )
                .order_by(Run.started_at.desc().nulls_last())
                .limit(20)
            )
        ]
        if not run_ids:
            return []
        rows = list(
            db.execute(
                select(Message)
                .where(Message.run_id.in_(run_ids))
                .order_by(Message.created_at, Message.seq)
            ).scalars()
        )
    finally:
        db.close()

    grouped: dict[str, list[Message]] = defaultdict(list)
    for m in rows:
        grouped[m.run_id].append(m)

    chrono = list(reversed(run_ids))  # 从旧到新
    recent = chrono[-max(1, full_runs) :]  # 最近 N 轮：完整回放（含工具正文）
    older = chrono[: len(chrono) - len(recent)]  # 更早：只留文本 + 检索摘要

    out: list[dict] = []
    for run_id in older:
        for m in grouped.get(run_id, []):
            if m.role == "user":
                out.append({"role": "user", "content": m.content})
            elif m.role == "assistant" and (m.content or "").strip():
                out.append({"role": "assistant", "content": m.content})
        notes = _run_notes(grouped.get(run_id, []))
        if notes:
            out.append({"role": "system", "content": "[历史检索摘要]\n" + "\n".join(notes)})

    for run_id in recent:
        out.extend(_rebuild_run(grouped.get(run_id, [])))

    return _trim_tool_results(out, tool_budget)


def _run_notes(rows: list[Message]) -> list[str]:
    """把旧轮的工具调用压成一行一条的摘要（不含正文）。"""
    notes: list[str] = []
    for m in rows:
        if m.role != "assistant" or not m.tool_calls_json:
            continue
        try:
            calls = json.loads(m.tool_calls_json)
        except ValueError:
            continue
        stamp = m.created_at.strftime("%m-%d %H:%M") if m.created_at else ""
        for c in calls:
            fn = c.get("function") or {}
            name = fn.get("name") or "tool"
            args = (fn.get("arguments") or "").replace("\n", " ")[:80]
            notes.append(f"- {stamp} {name}({args}) → 结果正文已省略")
    return notes


def _rebuild_run(rows: list[Message]) -> list[dict]:
    """把一轮消息还原成 OpenAI 形状，并保证 tool 调用成组。"""
    out: list[dict] = []
    i = 0
    while i < len(rows):
        m = rows[i]
        if m.role == "user":
            out.append({"role": "user", "content": m.content})
            i += 1
            continue
        if m.role != "assistant":
            i += 1  # 孤儿 tool 行（理论不该出现）：丢掉，否则上游 400
            continue

        calls: list[dict] = []
        if m.tool_calls_json:
            try:
                calls = json.loads(m.tool_calls_json)
            except ValueError:
                calls = []
        item: dict = {"role": "assistant", "content": m.content or ""}
        if calls:
            item["tool_calls"] = calls
        out.append(item)
        i += 1
        if not calls:
            continue

        wanted = {c.get("id") for c in calls if c.get("id")}
        answered: set[str] = set()
        while i < len(rows) and rows[i].role == "tool":
            t = rows[i]
            if t.tool_call_id in wanted:
                out.append(
                    {"role": "tool", "tool_call_id": t.tool_call_id, "content": t.content}
                )
                answered.add(t.tool_call_id)
            i += 1
        # 中断/超时导致缺失的调用补一条占位，避免「悬空 tool_calls」
        for cid in wanted - answered:
            out.append(
                {"role": "tool", "tool_call_id": cid, "content": "（该工具执行未完成）"}
            )
    return out


def _trim_tool_results(messages: list[dict], budget: int) -> list[dict]:
    """工具结果超预算时，从最旧的整组开始换成一句占位说明。

    必须整组替换：只删 tool 行、留下 assistant 的 tool_calls 会破坏配对。
    """
    total = sum(len(m.get("content") or "") for m in messages if m["role"] == "tool")
    if total <= budget:
        return messages

    out: list[dict] = []
    i = 0
    while i < len(messages):
        m = messages[i]
        if m["role"] != "assistant" or not m.get("tool_calls"):
            out.append(m)
            i += 1
            continue

        j = i + 1
        while j < len(messages) and messages[j]["role"] == "tool":
            j += 1
        group = messages[i:j]
        cost = sum(len(g.get("content") or "") for g in group if g["role"] == "tool")

        if total > budget and cost:
            total -= cost
            if m.get("content"):
                out.append({"role": "assistant", "content": m["content"]})
            out.append(
                {"role": "system", "content": "[早前的工具结果已省略，需要时可重新调用]"}
            )
        else:
            out.extend(group)
        i = j
    return out


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