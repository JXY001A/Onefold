"""文档域：上传文件、切片、产物、解析队列与技能包。"""

from datetime import datetime

from pgvector.sqlalchemy import HALFVEC

from .common import (
    Base,
    Boolean,
    DateTime,
    Index,
    Integer,
    Mapped,
    String,
    Text,
    mapped_column,
    now,
    sql_text,
)


class KnowledgeBase(Base):
    """知识库作用域：public（公共）或 personal（每人一个）。"""

    __tablename__ = "knowledge_bases"
    __table_args__ = (
        # 只允许一个公共库；owner_key=NULL 在普通唯一索引里不生效，必须用部分索引
        Index("uq_kb_public", "kind", unique=True,
              postgresql_where=sql_text("kind = 'public'")),
        Index("uq_kb_personal_owner", "owner_key", unique=True,
              postgresql_where=sql_text("kind = 'personal'")),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16))       # public | personal
    name: Mapped[str] = mapped_column(String(128))
    owner_key: Mapped[str | None] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Document(Base):
    """上传文档元信息；原始二进制放 data/uploads，不进数据库。"""

    __tablename__ = "documents"
    __table_args__ = (
        # 文档列表和检索都按 owner + kind + status 过滤
        Index("ix_documents_owner_kind_status", "owner_key", "kind", "status"),
        Index("ix_documents_kb_status", "kb_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # 兼容旧数据；新逻辑统一按 owner_key 做归属
    user_id: Mapped[str | None] = mapped_column(String(36), index=True)
    # kb_id 是访问控制的真正来源；owner_key 继续作为冗余作用域键
    kb_id: Mapped[str | None] = mapped_column(String(36), index=True)
    owner_key: Mapped[str | None] = mapped_column(String(80), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(36))
    filename: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(512))
    size: Mapped[int] = mapped_column(Integer, default=0)
    mime: Mapped[str | None] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(16), default="temp")
    status: Mapped[str] = mapped_column(String(16), default="uploaded")
    error: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Chunk(Base):
    """父子块：parent 给模型上下文，child 负责检索。"""

    __tablename__ = "chunks"
    __table_args__ = (
        Index("ix_chunks_owner_status", "owner_key", "embed_status"),
        Index("ix_chunks_document_index", "document_id", "chunk_index"),
        # 同一文档内相同内容只存一次，避免重复上传产生重复召回
        Index("uq_chunks_document_hash", "document_id", "kind", "content_hash", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), index=True)
    owner_key: Mapped[str | None] = mapped_column(String(80), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), index=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), index=True)
    kind: Mapped[str] = mapped_column(String(16), default="child")
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    heading_path: Mapped[str | None] = mapped_column(Text)
    context_prefix: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    search_text: Mapped[str | None] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer)
    token_count: Mapped[int | None] = mapped_column(Integer)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    # 只给 child 向量；parent 不重复 embedding
    embedding: Mapped[list[float] | None] = mapped_column(HALFVEC(1024))
    embed_model: Mapped[str | None] = mapped_column(String(64))
    embed_status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str | None] = mapped_column(String(36), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36))
    path: Mapped[str] = mapped_column(String(512))
    size: Mapped[int] = mapped_column(Integer, default=0)
    kind: Mapped[str | None] = mapped_column(String(32))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str | None] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(64))
    version: Mapped[str | None] = mapped_column(String(32))
    path: Mapped[str] = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class DocumentJob(Base):
    """文档解析/嵌入任务队列，由 index-worker 处理。"""

    __tablename__ = "document_jobs"
    __table_args__ = (
        Index("ix_document_jobs_status_created", "status", "created_at"),
        # worker 抢占：pending + 到点 + 最早创建
        Index("ix_document_jobs_claim", "status", "run_after", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), index=True)
    owner_key: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    stage: Mapped[str | None] = mapped_column(String(16))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    run_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))