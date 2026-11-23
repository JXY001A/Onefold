"""按会话读取消息，供前端渲染历史（含工具步骤）。

工具行的正文动辄几千字且以标签开头，这里只回审计表里的短文案与成败，
供前端画一行痕迹；老会话没有 data_json 时从正文里还原标题与链接兜底。
"""

import html
import json
import re

from sqlalchemy import select

from ..db import SessionLocal
from ..models import Message, Run, ToolCall

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