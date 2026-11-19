"""联网搜索 / 网页抓取：把 DeepSeek 官方接口包装成给模型看的文本。

两个函数都返回 (文本, 条数/字数, 结构化结果)：
    - 文本进 tool 消息，供模型阅读（网页内容一律经 wrap_external 标注）
    - 结构化结果进 tool_calls.data_json，供前端侧栏展示「链接 + 简介」
"""

import re

from ...config import settings
from .client import post_tool
from .guard import check_url, wrap_external

MAX_TITLE = 120
# 给前端列表展示的简介长度（给模型看的正文仍按 search_snippet_chars 截断）
BRIEF_CHARS = 200


def _clean(text: str) -> str:
    """侧栏简介里去掉 Markdown 的标题/引用符号，避免 ### 日出日落、> 11 多云 这类噪声。"""
    lines = [ln.strip().lstrip(">#").strip() for ln in text.splitlines()]
    return re.sub(r"\s*>\s*", " ", " ".join(" ".join(lines).split())).strip()


async def search(
    query: str,
    count: int | None = None,
    ori_question: str | None = None,
) -> tuple[str, int, dict]:
    """返回 (给模型的搜索结果, 命中条数, 给前端的结构化结果)。"""
    q = (query or "").strip()[:128]
    if not q:
        raise ValueError("搜索词不能为空")

    n = min(max(count or settings.search_count, 1), 50)
    payload: dict = {"query": q, "count": n, "need_content": False}
    # 带上用户原始问题，官方会用它更好地理解搜索意图
    if ori_question:
        payload["ori_question"] = ori_question[:128]

    data = await post_tool("/v1/tools/search", payload)
    # 相关度低于阈值的多半是广告/无关页，丢掉能省上下文也少噪音
    items = [
        r
        for r in (data.get("results") or [])
        if (r.get("rerank_score") or 0) >= settings.search_min_score
    ]
    brief: dict = {"kind": "search", "query": q, "items": []}
    if not items:
        return (
            "没有找到相关结果。可以换个关键词，或用 site:/after: 等语法缩小范围。",
            0,
            brief,
        )

    blocks = []
    for i, r in enumerate(items, 1):
        summary = (r.get("summary") or r.get("snippet") or "").strip()
        body = summary[: settings.search_snippet_chars]
        if len(summary) > len(body):
            body += "…"
        site = r.get("site_name") or ""
        date = (r.get("date") or "")[:10]
        meta = " · ".join(str(x) for x in (site, date) if x)
        title = (r.get("title") or "无标题")[:MAX_TITLE]
        head = f"[{i}] {title}" + (f"（{meta}）" if meta else "")
        blocks.append(f"{head}\n{wrap_external(r.get('url') or '', body)}")
        brief["items"].append(
            {
                "title": title,
                "url": r.get("url") or "",
                "site": site,
                "date": date,
                "snippet": _clean(body[:BRIEF_CHARS]),
            }
        )

    return "\n\n".join(blocks), len(items), brief


async def fetch(url: str) -> tuple[str, int, dict]:
    """返回 (带标签的网页正文, 正文长度, 给前端的结构化结果)。"""
    target = check_url(url)
    data = await post_tool("/v1/tools/fetch", {"url": target})

    content = (data.get("content") or "").strip()
    title = (data.get("title") or "").strip()
    brief = {"kind": "fetch", "url": target, "title": title or target, "chars": 0}
    if not content:
        return "该网页没有可提取的正文。", 0, brief

    title = title or "无"
    clipped = content[: settings.fetch_max_chars]
    text = f"标题：{title}\n{wrap_external(target, clipped)}"
    if len(content) > len(clipped):
        # 明确告诉模型「后面还有」，需要时它可以再调一次或让用户提供更多线索
        text += "\n（正文过长，已截断）"
    brief.update(title=title, chars=len(clipped), snippet=_clean(clipped[:BRIEF_CHARS]))
    return text, len(clipped), brief
