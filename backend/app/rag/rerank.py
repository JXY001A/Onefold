"""OpenRouter rerank 客户端；失败时返回 None，由调用方回退 RRF。"""

import httpx

from ..config import settings


def rerank(
    query: str,
    documents: list[str],
    ids: list[str],
    top_n: int = 5,
    model: str | None = None,
) -> list[tuple[str, float]] | None:
    """对候选逐对打分；结果保持 id 对应，失败不抛给聊天主链路。"""
    model = model or settings.rerank_model
    if not settings.rerank_enabled or not model or not settings.openrouter_api_key:
        return None
    if not documents or len(documents) != len(ids):
        return None

    url = "https://openrouter.ai/api/v1/rerank"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "query": query,
        "documents": documents,
        "top_n": min(max(1, top_n), len(documents)),
    }
    try:
        # trust_env=False：避免本机代理变量影响 API 请求
        with httpx.Client(trust_env=False, timeout=settings.embed_timeout_s) as client:
            response = client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return None
        results = response.json().get("results") or []
        ranked: list[tuple[str, float]] = []
        for item in results:
            index = item.get("index")
            if isinstance(index, int) and 0 <= index < len(ids):
                ranked.append((ids[index], float(item.get("relevance_score") or 0)))
        return ranked or None
    except (httpx.HTTPError, ValueError, TypeError):
        return None
