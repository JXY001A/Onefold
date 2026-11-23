"""记忆域：开关、记忆本体、提取队列与变更审计。"""

from datetime import datetime

from .common import (
    JSONB,
    Base,
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    Mapped,
    String,
    Text,
    mapped_column,
    now,
    sql_text,
)


class MemorySetting(Base):
    """记忆开关：登录用户与访客共用一张表，按 owner_key 区分。

    单独建表而不是往 users/guest_sessions 加列，是为了避免已有库在
    create_all 下不会自动 ALTER 的迁移问题。
    """

    __tablename__ = "memory_settings"

    owner_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sql_text("true"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MemoryItem(Base):
    """一条长期记忆：卡片（结构化事实）或笔记（带背景的事件/决定）。"""

    __tablename__ = "memory_items"
    __table_args__ = (
        # 同一用户的同一张卡片只能有一条 active；归档/删除的历史行不受限制
        Index(
            "uq_memory_card_active",
            "owner_key",
            "category",
            "key",
            unique=True,
            postgresql_where=sql_text("kind = 'card' AND status = 'active'"),
        ),
        # 笔记按指纹去重，避免同一段背景被反复写入
        Index(
            "uq_memory_note_fingerprint",
            "owner_key",
            "fingerprint",
            unique=True,
            postgresql_where=sql_text("kind = 'note' AND status = 'active'"),
        ),
        Index("ix_memory_owner_status", "owner_key", "status", "updated_at"),
        Index(
            "ix_memory_guest_ttl",
            "updated_at",
            postgresql_where=sql_text("owner_kind = 'guest' AND status = 'active'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(80), index=True)  # user:<id> 或 guest:<id>
    owner_kind: Mapped[str] = mapped_column(String(8))  # user / guest
    kind: Mapped[str] = mapped_column(String(8))  # card（结构化事实）/ note（带背景的笔记）
    category: Mapped[str | None] = mapped_column(String(32))  # profile/preference/project/...
    key: Mapped[str | None] = mapped_column(String(64))  # 卡片唯一键；笔记为空
    value: Mapped[dict | list | None] = mapped_column(JSONB)  # 卡片的结构化值；笔记为空
    text: Mapped[str] = mapped_column(Text)  # 给人看的描述，也是注入上下文的内容
    fingerprint: Mapped[str | None] = mapped_column(String(64))  # 笔记去重指纹；卡片为空
    confidence: Mapped[float] = mapped_column(Float, default=0.8)  # 模型置信度 0~1
    mention_count: Mapped[int] = mapped_column(Integer, default=1)  # 被提到次数，影响排序
    usage_count: Mapped[int] = mapped_column(Integer, default=0)  # 被注入对话的次数
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sql_text("false"))
    source_run_id: Mapped[str | None] = mapped_column(String(36))  # 来自哪一轮对话
    source_message_id: Mapped[str | None] = mapped_column(String(36))  # 来自哪条用户消息
    happened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 笔记记录的事件时间
    last_mentioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="active")  # active / deleted（软删除）
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MemoryJob(Base):
    """记忆提取任务队列；run_id 唯一，保证一轮对话只提取一次。"""

    __tablename__ = "memory_jobs"
    __table_args__ = (
        Index("uq_memory_jobs_run", "run_id", unique=True),
        Index(
            "ix_memory_jobs_claim",
            "status",
            "run_after",
            "priority",
            "created_at",
            postgresql_where=sql_text("status = 'pending'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(80), index=True)
    owner_kind: Mapped[str] = mapped_column(String(8))
    run_id: Mapped[str] = mapped_column(String(36))  # 唯一：一轮对话只提取一次
    conversation_id: Mapped[str | None] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/running/done/failed
    priority: Mapped[int] = mapped_column(Integer, default=0)  # 10 = 用户显式要求「记住」
    attempts: Mapped[int] = mapped_column(Integer, default=0)  # 已尝试次数，用于重试上限
    result: Mapped[str | None] = mapped_column(String(16))  # written/no_change/empty/skipped
    stats: Mapped[dict | None] = mapped_column(JSONB)  # 本次增删改计数
    run_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)  # 可执行时间（退避用）
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 抢单时间，用于回收僵尸任务
    locked_by: Mapped[str | None] = mapped_column(String(64))  # 哪个 worker 在处理
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MemoryEvent(Base):
    """记忆变更审计：谁在什么时候把哪条记忆改成了什么。"""

    __tablename__ = "memory_events"
    __table_args__ = (Index("ix_memory_events_owner", "owner_key", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(80), index=True)
    owner_kind: Mapped[str] = mapped_column(String(8))
    memory_id: Mapped[str | None] = mapped_column(String(36))  # 单条操作有值；清空时为 None
    action: Mapped[str] = mapped_column(String(16))  # add / update / delete
    old_value: Mapped[dict | None] = mapped_column(JSONB)  # 变更前快照
    new_value: Mapped[dict | None] = mapped_column(JSONB)  # 变更后快照
    source_run_id: Mapped[str | None] = mapped_column(String(36))
    actor: Mapped[str] = mapped_column(String(16), default="worker")  # worker（模型）/ user（手动）
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)