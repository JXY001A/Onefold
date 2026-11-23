"""RAG 召回层：词法候选、向量候选、父块读取。"""

from dataclasses import dataclass

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from ..models import Chunk, Document
from .bm25 import tokenize


@dataclass(frozen=True)
class Candidate:
    id: str
    document_id: str
    parent_id: str | None
    text: str
    filename: str
    page: int | None
    heading_path: str
    score: float = 0.0


def scope_filter(owner_key: str, conversation_id: str | None):
    """临时文档限当前会话或未绑定会话；个人文档限 owner。"""
    temp_scope = and_(
        Document.kind == "temp",
        or_(
            Document.conversation_id == conversation_id,
            Document.conversation_id.is_(None),
        ),
    )
    return and_(
        Document.owner_key == owner_key,
        Document.status == "ready",
        or_(temp_scope, Document.kind == "personal"),
    )


def lexical_candidates(
    db: Session,
    query: str,
    owner_key: str,
    conversation_id: str | None,
    limit: int,
) -> list[Candidate]:
    """tsvector 召回 child；中文由 jieba 分词后写入 search_text。"""
    terms = tokenize(query)
    if not terms:
        return []
    ts_query = " ".join(terms)
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
            rank,
        )
        .join(Document, Document.id == Chunk.document_id)
        .where(
            scope_filter(owner_key, conversation_id),
            Chunk.kind == "child",
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
) -> list[Candidate]:
    """pgvector 余弦距离召回 child；查询向量由调用方生成。"""
    distance = Chunk.embedding.cosine_distance(vector).label("distance")
    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Chunk.parent_id,
            Chunk.text,
            Chunk.page,
            Chunk.heading_path,
            Document.filename,
            distance,
        )
        .join(Document, Document.id == Chunk.document_id)
        .where(
            scope_filter(owner_key, conversation_id),
            Chunk.kind == "child",
            Chunk.embed_status == "ready",
            Chunk.embedding.is_not(None),
        )
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
