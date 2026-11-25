"""knowledge bases

Revision ID: 0a1b2c3d4e5f
Revises: 8f2c1d4e5a6b
Create Date: 2026-11-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0a1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "8f2c1d4e5a6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """公共库 + 个人库；临时文档仍归个人库生命周期。"""
    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("owner_key", sa.String(80), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_bases_owner_key", "knowledge_bases", ["owner_key"])
    op.create_index(
        "uq_kb_public",
        "knowledge_bases",
        ["kind"],
        unique=True,
        postgresql_where=sa.text("kind = 'public'"),
    )
    op.create_index(
        "uq_kb_personal_owner",
        "knowledge_bases",
        ["owner_key"],
        unique=True,
        postgresql_where=sa.text("kind = 'personal'"),
    )
    op.execute(
        "INSERT INTO knowledge_bases "
        "(id, kind, name, owner_key, status, created_at, updated_at) "
        "VALUES ('public', 'public', '公共知识库', NULL, 'active', now(), now())"
    )

    op.add_column("documents", sa.Column("kb_id", sa.String(36), nullable=True))
    op.create_index("ix_documents_kb_id", "documents", ["kb_id"])
    op.create_index("ix_documents_kb_status", "documents", ["kb_id", "status"])

    # 每个已有 owner 懒生成一个个人知识库；md5 前 32 位作为稳定 id
    op.execute(
        """
        INSERT INTO knowledge_bases
            (id, kind, name, owner_key, status, created_at, updated_at)
        SELECT substr(md5(owner_key), 1, 32), 'personal', '个人知识库',
               owner_key, 'active', now(), now()
        FROM (
            SELECT DISTINCT owner_key
            FROM documents
            WHERE owner_key IS NOT NULL AND owner_key <> 'public'
        ) x
        """
    )
    op.execute(
        """
        UPDATE documents d
        SET kb_id = kb.id
        FROM knowledge_bases kb
        WHERE kb.kind = 'personal'
          AND kb.owner_key = d.owner_key
          AND d.kb_id IS NULL
        """
    )
    # 已有 public 文档（如果有）归公共库；新逻辑不会产生这种历史数据
    op.execute(
        """
        UPDATE documents
        SET kb_id = 'public', owner_key = 'public',
            conversation_id = NULL, expires_at = NULL, kind = 'public'
        WHERE kind = 'public' AND kb_id IS NULL
        """
    )


def downgrade() -> None:
    """回滚知识库结构；文档本身不删除。"""
    op.drop_index("ix_documents_kb_status", table_name="documents")
    op.drop_index("ix_documents_kb_id", table_name="documents")
    op.drop_column("documents", "kb_id")

    op.drop_index("uq_kb_personal_owner", table_name="knowledge_bases")
    op.drop_index("uq_kb_public", table_name="knowledge_bases")
    op.drop_index("ix_knowledge_bases_owner_key", table_name="knowledge_bases")
    op.drop_table("knowledge_bases")
