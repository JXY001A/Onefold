"""对词法候选做 BM25 重排；不建全量内存索引。"""

import jieba
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    """中文用 jieba 搜索模式切词，英文/数字保留原词。"""
    return [token for token in jieba.cut_for_search(text or "") if token.strip()]


def bm25_rank(
    query: str,
    documents: list[str],
    top_n: int,
) -> list[tuple[int, float]]:
    """返回 (原文档下标, 分数)，按分数从高到低。"""
    query_tokens = tokenize(query)
    if not query_tokens or not documents:
        return []

    valid: list[tuple[int, list[str]]] = []
    for index, text in enumerate(documents):
        tokens = tokenize(text)
        if tokens:
            valid.append((index, tokens))
    if not valid:
        return []

    bm25 = BM25Okapi([tokens for _, tokens in valid])
    scores = bm25.get_scores(query_tokens)
    ranked = [
        (valid[i][0], float(scores[i]))
        for i in range(len(valid))
        if float(scores[i]) > 0
    ]
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[: max(1, top_n)]
