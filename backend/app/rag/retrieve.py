"""文档混合检索：词法 + 向量 + BM25 + RRF + 可选 rerank。"""

from dataclasses import dataclass
import logging

from sqlalchemy.orm import Session

from ..config import settings
from ..db import SessionLocal
from .bm25 import bm25_rank
from .embed import embed_texts
from .query import Candidate, lexical_candidates, load_parents, vector_candidates
from .rerank import rerank
from .rrf import rrf_fuse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    text: str
    filename: str = ""
    page: int | None = None
    heading_path: str = ""
    kb_id: str = ""
    scope: str = "personal"
    score: float = 0.0
    parent_id: str | None = None


def _bm25_ids(query: str, candidates: list[Candidate]) -> list[str]:
    """先做 BM25 候选重排；没有命中时保留词法原顺序。"""
    ranked = bm25_rank(query, [c.text for c in candidates], settings.rag_bm25_top)
    return [candidates[index].id for index, _ in ranked] or [c.id for c in candidates]


def _rerank_ids(query: str, candidates: list[Candidate], limit: int) -> list[tuple[str, float]]:
    """rerank 失败返回空列表，调用方继续使用 RRF。"""
    ranked = rerank(
        query,
        [c.text for c in candidates],
        [c.id for c in candidates],
        top_n=limit,
    )
    return ranked or []


def _expand(
    candidates: list[Candidate],
    rank_scores: dict[str, float],
    parent_map: dict,
    top_k: int,
) -> list[RetrievedChunk]:
    """命中 child 后返回 parent 文本；同一 parent 只保留一次。"""
    out: list[RetrievedChunk] = []
    seen: set[str] = set()
    for candidate in candidates:
        parent = parent_map.get(candidate.parent_id or "")
        key = parent.id if parent else candidate.id
        if key in seen:
            continue
        seen.add(key)
        text = (parent.text if parent else candidate.text) or candidate.text
        out.append(
            RetrievedChunk(
                chunk_id=candidate.id,
                document_id=candidate.document_id,
                text=text,
                filename=candidate.filename,
                page=candidate.page,
                heading_path=candidate.heading_path,
                kb_id=candidate.kb_id,
                scope=candidate.scope,
                score=rank_scores.get(candidate.id, candidate.score),
                parent_id=parent.id if parent else candidate.parent_id,
            )
        )
        if len(out) >= top_k:
            break
    return out


def retrieve(
    query: str,
    owner_key: str,
    conversation_id: str | None = None,
    top_k: int | None = None,
    db: Session | None = None,
) -> list[RetrievedChunk]:
    """检索文档片段；任何外部依赖失败都退化为可用的部分结果。"""
    if not settings.rag_enabled or not query.strip() or not owner_key:
        return []
    top_k = max(1, top_k or settings.rag_top_k)
    own_session = db is None
    db = db or SessionLocal()
    try:
        # 词法优先级高于向量
        lexical = lexical_candidates(
            db, query, owner_key, conversation_id, settings.rag_lexical_candidates
        )
        vector: list[Candidate] = []
        try:
            vector = vector_candidates(
                db,
                embed_texts([query])[0],
                owner_key,
                conversation_id,
                settings.rag_vector_top,
                settings.rag_vector_max_distance,
            )
        except Exception:
            # 查询 embedding 失败时只用词法，不让聊天整体失败
            vector = []

        if not lexical and not vector:
            return []

        by_id = {candidate.id: candidate for candidate in lexical + vector}
        lexical_ids = _bm25_ids(query, lexical) if lexical else []
        vector_ids = [candidate.id for candidate in vector]
        fused = rrf_fuse(
            [lexical_ids, vector_ids],
            k=settings.rag_rrf_k,
            limit=max(top_k * 4, 20),
        )
        ordered = [by_id[item_id] for item_id, _ in fused if item_id in by_id]
        scores = {item_id: score for item_id, score in fused}

        # rerank 只对融合后的前 20 条做，失败就保持 RRF 顺序
        if settings.rerank_enabled and ordered:
            reranked = _rerank_ids(query, ordered[:20], top_k)
            if reranked:
                # rerank 是最终相关度判断：低于阈值的候选不再注入 RAG
                rerank_scores = {
                    item_id: score
                    for item_id, score in reranked
                    if score >= settings.rag_rerank_min_score
                }
                if not rerank_scores:
                    return []
                ordered = [item for item in ordered if item.id in rerank_scores]
                ordered.sort(key=lambda item: rerank_scores[item.id], reverse=True)
                # scores 原本只有 RRF 融合分；用 rerank 分覆盖被保留的候选，
                # 下游 _expand 会把它写进 RetrievedChunk。
                scores.update(rerank_scores)

        parent_map = load_parents(
            db, [item.parent_id for item in ordered if item.parent_id]
        )
        return _expand(ordered, scores, parent_map, top_k)
    except Exception:
        # RAG 是聊天增强，不是主链路：数据库/扩展异常时退化为“无参考资料”
        logger.exception("rag retrieve failed: owner=%s", owner_key)
        return []
    finally:
        if own_session:
            db.close()
