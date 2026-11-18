"""检索（骨架）：BM25 + 向量 + RRF + rerank。

TODO:
1. 分块后写入 chunks 表与 hnswlib 索引
2. query → jieba 分词 → BM25 top-50
3. query → bge-m3 → hnswlib top-50
4. RRF(k=60) 融合 → bge-reranker-v2-m3 重排 → top_k
5. 返回带 filename/page 的引用信息
"""

from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    text: str
    filename: str = ""
    page: int | None = None
    score: float = 0.0


def retrieve(
    query: str,
    user_id: str | None = None,
    conversation_id: str | None = None,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    _ = (query, user_id, conversation_id, top_k)
    return []
