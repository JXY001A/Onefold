"""数据表。字段与 docs/architecture.md 的数据模型保持一致。"""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """数据库读出的时间可能不带时区，统一按 UTC 处理后再参与计算。"""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class User(Base):
    """登录用户。role 决定权限：

        member      普通成员（注册即得）
        admin       管理员（由超管指定），可看审批/用量/run 详情
        superadmin  超管（手动写库），额外可改角色与停用账号

    账号以邮箱为主（email 唯一），username 只作展示昵称；
    早期没有邮箱的账号（如手动写入的超管）仍可用用户名登录。
    游客不在本表：游客是 guest_sessions 里的一行，有效角色由身份类型决定。
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # 唯一但可空：早期账号没有邮箱，PG 允许多个 NULL 并存
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="member")
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    # 改密时间：比这更早签发的 JWT 一律作废（deps.current_principal 校验 iat）
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EmailCode(Base):
    """邮箱验证码：注册与重置密码共用同一套。

    安全约定：
        - 只存 sha256(email + code + jwt_secret)，库里看不到明文码；
        - 一条码用一次即置 used_at，防重放；
        - 错误次数记在 attempts 上，超过上限作废，挡暴力枚举 6 位数字。
    """

    __tablename__ = "email_codes"
    __table_args__ = (Index("ix_email_codes_lookup", "email", "purpose", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    purpose: Mapped[str] = mapped_column(String(16))  # register / reset
    code_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    sent_ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AccessRequest(Base):
    __tablename__ = "access_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(64))
    contact: Mapped[str | None] = mapped_column(String(128))
    purpose: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GuestSession(Base):
    """匿名访客身份：每个浏览器一条，30 天滑动续期（每次访问顺延 expires_at）。"""

    __tablename__ = "guest_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ip: Mapped[str | None] = mapped_column(String(64), index=True)
    user_agent: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Visit(Base):
    """访问记录：一次「进入 → 停留 → 离开」，供后续用户画像分析。

    身份同样用 owner_key，因此同一访客跨天访问能靠 guest_id 串成一条轨迹。
    IP / UA 由服务端读取；屏幕、语言、时区、来源页等只有浏览器知道，由前端上报。
    """

    __tablename__ = "visits"
    __table_args__ = (
        # 画像查询常见入口：某个身份最近的访问记录
        Index("ix_visits_owner_entered", "owner_key", "entered_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(80), index=True)
    # user / guest：聚合时不必再拆 owner_key 前缀
    kind: Mapped[str] = mapped_column(String(8))

    # ── 网络与设备 ──────────────────────────────────────────
    ip: Mapped[str | None] = mapped_column(String(64), index=True)
    user_agent: Mapped[str | None] = mapped_column(String(255))
    device: Mapped[str | None] = mapped_column(String(16))  # desktop / mobile / tablet / bot
    os: Mapped[str | None] = mapped_column(String(32))
    browser: Mapped[str | None] = mapped_column(String(32))
    screen: Mapped[str | None] = mapped_column(String(16))  # 1920x1080（前端上报）
    language: Mapped[str | None] = mapped_column(String(32))  # zh-CN
    timezone: Mapped[str | None] = mapped_column(String(64))  # Asia/Shanghai

    # ── 来源 ────────────────────────────────────────────────
    referrer: Mapped[str | None] = mapped_column(String(255))
    entry_path: Mapped[str | None] = mapped_column(String(255))  # 进入时所在路由

    # ── 进出时间 ────────────────────────────────────────────
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # 停留秒数：离开时由 entered_at / left_at 算出，省得每次查询都做时间差
    duration_s: Mapped[int | None] = mapped_column(Integer)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(36), index=True)
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


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(36))
    filename: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(512))
    size: Mapped[int] = mapped_column(Integer, default=0)
    mime: Mapped[str | None] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(16), default="temp")
    status: Mapped[str] = mapped_column(String(16), default="uploaded")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), index=True)
    text: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer)
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


class UsageDaily(Base):
    __tablename__ = "usage_daily"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    day: Mapped[str] = mapped_column(String(10), primary_key=True)
    messages: Mapped[int] = mapped_column(Integer, default=0)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    tool_calls: Mapped[int] = mapped_column(Integer, default=0)
    docs: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(32))
    target: Mapped[str | None] = mapped_column(String(128))
    detail_json: Mapped[dict | None] = mapped_column(JSON)
    ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
