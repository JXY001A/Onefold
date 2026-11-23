"""把库里的消息行还原成 OpenAI 形状，并保证 tool 调用成组。

上游要求 tool 消息紧跟带 tool_calls 的 assistant，少一条就 400，
因此这里按「组」重建、按「组」裁剪。
"""

import json

from ..models import Message


def run_notes(rows: list[Message]) -> list[str]:
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


def rebuild_run(rows: list[Message]) -> list[dict]:
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


def trim_tool_results(messages: list[dict], budget: int) -> list[dict]:
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