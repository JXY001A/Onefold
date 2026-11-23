"""对话域：会话、每轮执行、消息、工具审计与历史摘要。"""

from datetime import datetime

from .common import (
    Base,
    DateTime,
    Float,
    Index,
    Integer,
    Mapped,
    String,
    Text,
    mapped_column,
    now,
)


class Conversation(Base):
    """会话元信息：会话列表、标题与活跃时间的来源。

    层级：conversations（会话）→ runs（每轮执行）→ messages（消息）。
    归属统一用 owner_key："user:<id>"（登录用户）/ "guest:<id>"（访客），
    与 Principal.lock_key 格式一致，两种身份走同一套查询与鉴权规则。
    """

    __tablename__ = "conversations"
    __table_args__ = (
        # 列表查询固定是「某归属 + 按活跃时间倒序 + 近 N 天」，复合索引一次命中
        Index("ix_conversations_owner_updated", "owner_key", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str | None] = mapped_column(String(128))
    # 会话级记忆快照：整个会话复用，避免自动记忆更新打断 KV Cache
    memory_snapshot: Mapped[str | None] = mapped_column(Text)
    memory_snapshot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # 已压缩到哪一轮；为 0 表示还没压缩
    summarized_until_turn_no: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (
        # 会话内单调递增的轮次号；UUID 不适合做范围查询
        Index("uq_runs_conversation_turn", "conversation_id", "turn_no", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(36), index=True)
    turn_no: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="queued")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str | None] = mapped_column(Text)


class Message(Base):
    """对话消息：既是「模型看到的上下文」，也是「前端渲染的历史」。

    role 三种取值：
        user       用户提问
        assistant  模型输出；tool_calls_json 非空时表示这一步要调用工具
        tool       工具执行结果；tool_call_id 指回 assistant 里的那一次调用

    为什么工具调用也要落 messages 表：OpenAI 协议要求 tool 消息紧跟
    带 tool_calls 的 assistant 消息，两者必须成组出现。只有把整组都存进库，
    下一轮重建上下文时才能 1:1 还原，否则会出现「孤儿 tool 消息」导致上游 400。

    seq 是 run 内的步骤序号（1 起），同一事务写入时 created_at 可能相同，
    排序必须靠它；早期数据的 seq=0，按 created_at 排也仍然正确。
    """

    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_run_seq", "run_id", "seq"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    # —— 工具循环相关（非工具消息全部为 NULL）——
    seq: Mapped[int] = mapped_column(Integer, default=0)
    # 上游返回的调用 ID，长度不定，不要塞进 String(36)
    tool_call_id: Mapped[str | None] = mapped_column(String(64))
    tool_name: Mapped[str | None] = mapped_column(String(64))
    # 仅 assistant 行：本步要调的工具列表 [{"id","name","arguments"}]
    tool_calls_json: Mapped[str | None] = mapped_column(Text)


class ToolCall(Base):
    """工具调用审计日志：运营视角（谁、何时、调了什么、多久、成没成）。

    与 messages 表职责分开，不重复存正文：
        messages  存「模型要回放的完整内容」（含网页正文，会撑大库）
        tool_calls 存「可统计的摘要」（结果只留前 200 字）
    """

    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    tool_name: Mapped[str] = mapped_column(String(64))
    args_json: Mapped[str | None] = mapped_column(Text)
    result_summary: Mapped[str | None] = mapped_column(Text)
    # 结构化结果（搜索结果列表 / 抓取页信息），供前端侧栏展示链接与简介
    data_json: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(16))
    elapsed_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    # —— 与 messages 对齐：便于从审计行回溯到具体对话步骤 ——
    llm_call_id: Mapped[str | None] = mapped_column(String(64))
    step: Mapped[int] = mapped_column(Integer, default=0)
    # 失败原因（超时 / 上游 429 / 地址被拒 等），成功时为 NULL
    error: Mapped[str | None] = mapped_column(Text)


class ConversationSummary(Base):
    """历史会话摘要：按 turn_no 区间生成，不可再压缩。"""

    __tablename__ = "conversation_summaries"
    __table_args__ = (
        Index(
            "uq_conversation_summaries_range",
            "conversation_id",
            "from_turn_no",
            "to_turn_no",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(36), index=True)
    owner_key: Mapped[str] = mapped_column(String(80), index=True)
    from_turn_no: Mapped[int] = mapped_column(Integer)
    to_turn_no: Mapped[int] = mapped_column(Integer)
    from_run_id: Mapped[str | None] = mapped_column(String(36))
    to_run_id: Mapped[str | None] = mapped_column(String(36))
    summary: Mapped[str] = mapped_column(Text)
    summary_tokens: Mapped[int | None] = mapped_column(Integer)
    source_tokens: Mapped[int | None] = mapped_column(Integer)
    model: Mapped[str | None] = mapped_column(String(64))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)