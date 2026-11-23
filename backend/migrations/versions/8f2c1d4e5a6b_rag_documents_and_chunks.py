"""rag documents and chunks

Revision ID: 8f2c1d4e5a6b
Revises: 6345b29b1042
Create Date: 2026-11-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import HALFVEC


revision: str = "8f2c1d4e5a6b"
down_revision: Union[str, Sequence[str], None] = "6345b29b1042"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """文档 RAG：归属、分块、向量和索引任务字段。"""
    # 向量类型来自扩展，必须先于 embedding 字段创建
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("documents", sa.Column("owner_key", sa.String(80), nullable=True))
    op.add_column("documents", sa.Column("error", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("documents", sa.Column("content_hash", sa.String(64), nullable=True))
    op.create_index("ix_documents_owner_kind_status", "documents", ["owner_key", "kind", "status"])

    # 旧文档按 user_id 回填归属；没有 user_id 的历史行保持 NULL
    op.execute(
        "UPDATE documents SET owner_key = 'user:' || user_id "
        "WHERE owner_key IS NULL AND user_id IS NOT NULL"
    )

    op.add_column("chunks", sa.Column("owner_key", sa.String(80), nullable=True))
    op.add_column("chunks", sa.Column("parent_id", sa.String(36), nullable=True))
    op.add_column(
        "chunks",
        sa.Column("kind", sa.String(16), server_default="child", nullable=False),
    )
    op.add_column(
        "chunks",
        sa.Column("chunk_index", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("chunks", sa.Column("heading_path", sa.Text(), nullable=True))
    op.add_column("chunks", sa.Column("context_prefix", sa.Text(), nullable=True))
    op.add_column("chunks", sa.Column("search_text", sa.Text(), nullable=True))
    op.add_column("chunks", sa.Column("token_count", sa.Integer(), nullable=True))
    op.add_column("chunks", sa.Column("content_hash", sa.String(64), nullable=True))
    op.add_column("chunks", sa.Column("embedding", HALFVEC(1024), nullable=True))
    op.add_column("chunks", sa.Column("embed_model", sa.String(64), nullable=True))
    op.add_column(
        "chunks",
        sa.Column("embed_status", sa.String(16), server_default="pending", nullable=False),
    )
    op.execute(
        "UPDATE chunks c SET owner_key = d.owner_key "
        "FROM documents d WHERE c.document_id = d.id AND c.owner_key IS NULL"
    )
    op.create_index("ix_chunks_owner_status", "chunks", ["owner_key", "embed_status"])
    op.create_index("ix_chunks_document_index", "chunks", ["document_id", "chunk_index"])
    op.create_index(
        "uq_chunks_document_hash",
        "chunks",
        ["document_id", "kind", "content_hash"],
        unique=True,
    )
    op.execute(
        "CREATE INDEX ix_chunks_search_tsv ON chunks "
        "USING gin (to_tsvector('simple', coalesce(search_text, '')))"
    )

    op.add_column("document_jobs", sa.Column("run_after", sa.DateTime(timezone=True)))
    op.add_column("document_jobs", sa.Column("started_at", sa.DateTime(timezone=True)))
    op.add_column("document_jobs", sa.Column("finished_at", sa.DateTime(timezone=True)))
    op.create_index(
        "ix_document_jobs_claim",
        "document_jobs",
        ["status", "run_after", "created_at"],
    )


def downgrade() -> None:
    """回滚 RAG 结构；vector 扩展保留，避免影响其他使用方。"""
    op.drop_index("ix_document_jobs_claim", table_name="document_jobs")
    op.drop_column("document_jobs", "finished_at")
    op.drop_column("document_jobs", "started_at")
    op.drop_column("document_jobs", "run_after")

    op.execute("DROP INDEX IF EXISTS ix_chunks_search_tsv")
    op.drop_index("uq_chunks_document_hash", table_name="chunks")
    op.drop_index("ix_chunks_document_index", table_name="chunks")
    op.drop_index("ix_chunks_owner_status", table_name="chunks")
    for column in (
        "embed_status",
        "embed_model",
        "embedding",
        "content_hash",
        "token_count",
        "search_text",
        "context_prefix",
        "heading_path",
        "chunk_index",
        "kind",
        "parent_id",
        "owner_key",
    ):
        op.drop_column("chunks", column)

    op.drop_index("ix_documents_owner_kind_status", table_name="documents")
    for column in ("content_hash", "chunk_count", "page_count", "error", "owner_key"):
        op.drop_column("documents", column)
