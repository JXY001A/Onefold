"""记忆打分：决定哪些条目值得注入，以及注入时的先后顺序。

卡片不依赖 query；笔记一半权重给与当前问题的相关性。
所有分数都归一到 0~1，便于按权重线性组合。
"""

import math
import re
from datetime import datetime, timezone

from ..models import MemoryItem


def recency(value: datetime | None) -> float:
    """30 天半衰的新鲜度，返回 0~1。"""
    if value is None:
        return 0.0
    current = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    days = max(0.0, (datetime.now(timezone.utc) - current).total_seconds() / 86400)
    return math.exp(-math.log(2) * days / 30)


def log_weight(count: int | None, cap: int = 10) -> float:
    """把次数压成 0~1；第 10 次以后趋平，避免刷屏霸榜。"""
    return min(1.0, math.log1p(max(0, count or 0)) / math.log1p(cap))


def terms(text: str) -> set[str]:
    """轻量检索词：英文/数字词 + 中文二元组，够小数据量用。"""
    lowered = (text or "").lower()
    ascii_words = set(re.findall(r"[a-z0-9_]{2,}", lowered))
    han = re.findall(r"[\u4e00-\u9fff]", lowered)
    bigrams = {han[i] + han[i + 1] for i in range(len(han) - 1)}
    return ascii_words | bigrams


def relevance(query: str, text: str) -> float:
    """0~1 的相关性：整句包含直接给 1，否则按词重合比例。"""
    if not query or not text:
        return 0.0
    q = query.lower()
    t = text.lower()
    if q in t:
        return 1.0
    query_terms = terms(query)
    if not query_terms:
        return 0.0
    return len(query_terms & terms(text)) / len(query_terms)


def card_score(item: MemoryItem) -> float:
    """卡片排序权重（不依赖 query）：固定 > 置信度高 > 新近 > 被多次提到/使用。"""
    return (
        # pinned ：被用户强调记住的
        0.30 * (1.0 if item.pinned else 0.0)
        # confidence 可信度
        + 0.20 * max(0.0, min(1.0, item.confidence))
        # 上次被提及  或 最近更新时间
        + 0.15 * recency(item.last_mentioned_at or item.updated_at)
        # mention_count 提及次数
        + 0.20 * log_weight(item.mention_count)
        # usage_count 使用次数
        + 0.15 * log_weight(item.usage_count)
    )


def note_score(item: MemoryItem, query: str) -> float:
    """笔记排序权重：与当前问题相关占一半，其余看置信度、新近与使用频率。"""
    return (
        0.50 * relevance(query, item.text)
        + 0.15 * max(0.0, min(1.0, item.confidence))
        + 0.10 * recency(item.last_mentioned_at or item.updated_at)
        + 0.15 * log_weight(item.mention_count)
        + 0.10 * log_weight(item.usage_count)
    )