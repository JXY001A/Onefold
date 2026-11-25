"""Embedding 客户端：主地址失败时自动回退 OpenRouter。"""

import time

import httpx

from ..config import settings

RETRYABLE = {408, 429, 500, 502, 503, 504}
OPENROUTER_URL = "https://openrouter.ai/api/v1/embeddings"


class EmbeddingError(RuntimeError):
    """embedding 不可用；调用方应把文档任务标记为失败并重试。"""


def _request(batch: list[str], url: str, attempts: int) -> list[list[float]]:
    if not settings.openrouter_api_key:
        raise EmbeddingError("OPENROUTER_API_KEY 未配置")
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": settings.embed_model, "input": batch}
    last_error = "unknown"

    for attempt in range(max(1, attempts)):
        try:
            # trust_env=False：避免本机代理变量把请求带到错误的代理
            with httpx.Client(
                trust_env=False, timeout=min(settings.embed_timeout_s, 15)
            ) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            last_error = type(exc).__name__
        else:
            if response.status_code == 200:
                data = response.json().get("data") or []
                # 上游不保证按输入顺序返回，按 index 排回去
                data = sorted(data, key=lambda item: item.get("index", 0))
                vectors = [item.get("embedding") or [] for item in data]
                if len(vectors) != len(batch):
                    raise EmbeddingError("embedding 返回数量不匹配")
                if any(len(vector) != settings.embed_dim for vector in vectors):
                    raise EmbeddingError("embedding 维度不匹配")
                return vectors
            last_error = response.text[:180]
            if response.status_code not in RETRYABLE:
                raise EmbeddingError(f"embedding 失败：{response.status_code} {last_error}")

        if attempt + 1 < attempts:
            time.sleep(0.5 * (2**attempt))

    raise EmbeddingError(f"embedding 重试后失败：{last_error}")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """把文本分批送 embedding；主服务不可达时回退 OpenRouter。"""
    if not texts:
        return []
    primary = settings.embed_base_url.rstrip("/") + "/embeddings"
    # 本地/家里服务快速失败后切 OpenRouter；OpenRouter 自己也保留重试
    primary_attempts = 3 if "openrouter.ai" in primary else 1
    endpoints = [(primary, primary_attempts)]
    if "openrouter.ai" not in primary:
        endpoints.append((OPENROUTER_URL, 3))

    last_error: Exception | None = None
    for url, attempts in endpoints:
        try:
            vectors: list[list[float]] = []
            size = max(1, settings.embed_batch_size)
            for start in range(0, len(texts), size):
                vectors.extend(_request(texts[start : start + size], url, attempts))
            return vectors
        except EmbeddingError as exc:
            last_error = exc
    raise last_error or EmbeddingError("embedding 不可用")
