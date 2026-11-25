"""RAG 召回层：词法候选、向量候选、父块读取。"""

from dataclasses import dataclass

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Chunk, Document, KnowledgeBase
from ..services.knowledge_access import visible_kb_condition
from .bm25 import tokenize


@dataclass(frozen=True)
# 候选块
class Candidate:
    id: str
    document_id: str
    parent_id: str | None
    text: str
    filename: str
    page: int | None
    heading_path: str
    kb_id: str
    scope: str
    score: float = 0.0


def scope_filter(owner_key: str, conversation_id: str | None):
    """public 全量可读；personal 按 owner；temp 再按会话过滤。"""
    allow_public = settings.public_kb_guest_read or not owner_key.startswith("guest:")
    return and_(
        Document.status == "ready",
        Document.kb_id.is_not(None),
        visible_kb_condition(owner_key, allow_public),
        or_(
            Document.kind != "temp",
            Document.conversation_id.is_(None),
            Document.conversation_id == conversation_id,
        ),
    )


def lexical_candidates(
    db: Session,
    query: str,
    owner_key: str,
    conversation_id: str | None,
    limit: int,
) -> list[Candidate]:
    """tsvector 召回 child；中文由 jieba 分词后写入 search_text。"""
    # 分词
    terms = tokenize(query)
    if not terms:
        return []
    ts_query = " ".join(terms)
    # 文本入库时已由 jieba 切好（空格分隔）；用 simple 配置：只切词、转小写，
    # 不做词干化与停用词过滤，检索词原样匹配；且必须与下方 tsquery 配置一致才能算 rank。
    # coalesce 兜住 NULL：tsvector(NULL) 会让比较结果为 NULL，该行被静默漏掉。
    tsv = func.to_tsvector("simple", func.coalesce(Chunk.search_text, ""))
    tsq = func.websearch_to_tsquery("simple", ts_query)
    rank = func.ts_rank_cd(tsv, tsq).label("rank")
    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Chunk.parent_id,
            Chunk.text,
            Chunk.page,
            Chunk.heading_path,
            Document.filename,
            # doc_kind: 文档类型
            Document.kind.label("doc_kind"),
            # kb_kind: 知识库类型
            KnowledgeBase.id.label("kb_id"),
            KnowledgeBase.kind.label("kb_kind"),
            rank,
        )
        .join(Document, Document.id == Chunk.document_id)
        .join(KnowledgeBase, KnowledgeBase.id == Document.kb_id)
        .where(
            scope_filter(owner_key, conversation_id),
            Chunk.kind == "child",
            # tsvector @@ tsquery
            tsv.op("@@")(tsq),
        )
        .order_by(rank.desc())
        .limit(limit)
    )
    return [
        Candidate(
            id=row.id,
            document_id=row.document_id,
            parent_id=row.parent_id,
            text=row.text,
            filename=row.filename,
            page=row.page,
            heading_path=row.heading_path or "",
            kb_id=row.kb_id,
            scope="public" if row.kb_kind == "public" else (
                "temp" if row.doc_kind == "temp" else "personal"
            ),
            score=float(row.rank or 0),
        )
        for row in db.execute(stmt)
    ]


def vector_candidates(
    db: Session,
    vector: list[float],
    owner_key: str,
    conversation_id: str | None,
    limit: int,
    max_distance: float | None = None,
) -> list[Candidate]:
    """pgvector 余弦距离召回 child；超过 max_distance 的明显不相关块直接丢弃。"""

    # 向量距离；先粗筛，最终是否采用由 rerank 决定
    distance = Chunk.embedding.cosine_distance(vector)
    filters = [
        scope_filter(owner_key, conversation_id),
        Chunk.kind == "child",
        Chunk.embed_status == "ready",
        Chunk.embedding.is_not(None),
    ]
    if max_distance is not None:
        filters.append(distance <= max_distance)
    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Chunk.parent_id,
            Chunk.text,
            Chunk.page,
            Chunk.heading_path,
            Document.filename,
            Document.kind.label("doc_kind"),
            KnowledgeBase.id.label("kb_id"),
            KnowledgeBase.kind.label("kb_kind"),
            distance.label("distance"),
        )
        .join(Document, Document.id == Chunk.document_id)
        .join(KnowledgeBase, KnowledgeBase.id == Document.kb_id)
        .where(*filters)
        .order_by(distance)
        .limit(limit)
    )
    return [
        Candidate(
            id=row.id,
            document_id=row.document_id,
            parent_id=row.parent_id,
            text=row.text,
            filename=row.filename,
            page=row.page,
            heading_path=row.heading_path or "",
            kb_id=row.kb_id,
            scope="public" if row.kb_kind == "public" else (
                "temp" if row.doc_kind == "temp" else "personal"
            ),
            score=max(0.0, 1.0 - float(row.distance or 1.0)),
        )
        for row in db.execute(stmt)
    ]


def load_parents(db: Session, parent_ids: list[str]) -> dict[str, Chunk]:
    """一次取回选中的父块，避免逐条查询。"""
    if not parent_ids:
        return {}
    rows = db.execute(select(Chunk).where(Chunk.id.in_(set(parent_ids)))).scalars()
    return {row.id: row for row in rows}
