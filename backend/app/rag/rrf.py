"""Reciprocal Rank Fusion：融合词法和向量两路排名。"""


def rrf_fuse(
    rankings: list[list[str]],
    k: int = 60,
    limit: int | None = None,
) -> list[tuple[str, float]]:
    """每个 ranking 按名次贡献 1/(k+rank)，返回融合后的 id 和分数。"""
    scores: dict[str, float] = {}
    for ranking in rankings:
        seen: set[str] = set()
        for rank, item_id in enumerate(ranking, 1):
            # 同一路里重复 id 只算一次，避免重复结果被放大
            if item_id in seen:
                continue
            seen.add(item_id)
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)

    fused = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return fused[:limit] if limit else fused
