"""账号与访问域：用户、验证码、访客、访问记录、审计与用量。"""

from datetime import datetime

from .common import (
    JSON,
    Base,
    DateTime,
    Float,
    Index,
    Integer,
    Mapped,
    String,
    mapped_column,
    now,
)


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


class GuestSession(Base):
    """匿名访客身份：每个浏览器一条，30 天滑动续期（每次访问顺延 expires_at）。"""

    __tablename__ = "guest_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ip: Mapped[str | None] = mapped_column(String(64), index=True)
    user_agent: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


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