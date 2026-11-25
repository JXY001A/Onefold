"""文档索引：解析 → 父子分块 → embedding → 写 chunks。"""

from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete

from ..config import settings
from ..db import SessionLocal
from ..models import Chunk, Document
from .chunk import chunk_blocks
from .embed import embed_texts
from .parse import parse_document


def _file_hash(path: str) -> str:
    digest = sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _build_rows(doc: Document, specs, vectors: list[list[float]]) -> list[Chunk]:
    """把 ChunkSpec 变成 ORM 行；重复内容跳过，避免唯一索引冲突。"""
    rows: list[Chunk] = []
    seen: dict[tuple[str, str], str] = {}
    parent_ids: dict[int, str] = {}
    # 子块的 embedding 从头开始取
    child_vectors = iter(vectors)

    for spec in specs:
        key = (spec.kind, spec.content_hash)
        if key in seen:
            if spec.kind == "parent":
                parent_ids[spec.index] = seen[key]
            continue
        chunk_id = str(uuid4())
        seen[key] = chunk_id
        if spec.kind == "parent":
            parent_ids[spec.index] = chunk_id

        is_child = spec.kind == "child"
        rows.append(
            Chunk(
                id=chunk_id,
                document_id=doc.id,
                owner_key=doc.owner_key,
                user_id=doc.user_id,
                parent_id=parent_ids.get(spec.parent_index) if is_child else None,
                kind=spec.kind,
                chunk_index=spec.index,
                heading_path=spec.heading_path,
                text=spec.text,
                search_text=spec.search_text or None,
                page=spec.page,
                token_count=spec.token_count,
                content_hash=spec.content_hash,
                embedding=next(child_vectors) if is_child else None,
                embed_model=settings.embed_model if is_child else None,
                embed_status="ready" if is_child else "skipped",
            )
        )
    return rows


def index_document(document_id: str, owner_key: str) -> int:
    """重建一份文档的 chunks；失败抛异常，由 index-worker 记录并重试。"""
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None or doc.owner_key != owner_key:
            raise ValueError("文档不存在或归属不匹配")
        doc.status = "parsing"
        doc.error = None
        db.commit()

        blocks = parse_document(doc.path, doc.filename)
        specs = chunk_blocks(blocks)
        children = [spec.text for spec in specs if spec.kind == "child"]
        if not children:
            raise ValueError("文档没有可索引文本")
        vectors = embed_texts(children)

        # 新索引全部准备好后再替换旧 chunks，解析/embedding 失败不会先删旧数据
        db.execute(delete(Chunk).where(Chunk.document_id == doc.id))
        rows = _build_rows(doc, specs, vectors)
        db.add_all(rows)
        doc.status = "ready"
        doc.page_count = max((block.page or 0 for block in blocks), default=0) or None
        doc.chunk_count = len(rows)
        doc.content_hash = _file_hash(doc.path)
        db.commit()
        return len(rows)
    except Exception as exc:
        db.rollback()
        # 单独开一个事务记录失败，避免前面回滚把状态也丢掉
        with SessionLocal() as failed:
            doc = failed.get(Document, document_id)
            if doc is not None:
                doc.status = "failed"
                doc.error = f"{type(exc).__name__}: {str(exc)[:300]}"
                failed.commit()
        raise
    finally:
        db.close()
