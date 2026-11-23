"""邮箱验证码：签发、频控、校验。

安全要点：
    - 只存 sha256(email + code + jwt_secret)，库里看不到明文；
    - 6 位数字用 secrets 生成（不是 random），避免被预测；
    - 冷却 + 每小时/每日上限，挡住「拿我们当邮件轰炸机」；
    - 输错 5 次作废、用过作废，6 位数字才不至于被暴力枚举。
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import EmailCode, as_utc

PURPOSES = ("register", "reset")


class TooManyRequests(Exception):
    """发码过于频繁（映射成 HTTP 429）。"""


class InvalidCode(Exception):
    """验证码不存在 / 过期 / 错误次数超限（统一提示，不区分原因）。"""


def _hash(email: str, code: str) -> str:
    return hashlib.sha256(f"{email}:{code}:{settings.jwt_secret}".encode()).hexdigest()


def issue(db: Session, email: str, purpose: str, ip: str | None) -> str:
    """生成并入库一条验证码，返回明文码（只用于发信，不落库）。"""
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)

    rows = db.execute(
        select(EmailCode.created_at).where(
            EmailCode.email == email,
            EmailCode.purpose == purpose,
            EmailCode.created_at >= day_ago,
        )
    ).scalars().all()
    sent = [as_utc(t) for t in rows]
    # email 发送频率限制
    if any(t > now - timedelta(seconds=settings.email_code_cooldown_s) for t in sent):
        raise TooManyRequests("验证码刚发过，请稍后再试")
    # 一小时内仅允许发送 settings.email_code_hourly_max 数量的验证码
    hour_ago = now - timedelta(hours=1)
    if sum(1 for t in sent if t >= hour_ago) >= settings.email_code_hourly_max:
        raise TooManyRequests("获取过于频繁，请一小时后再试")
    if len(sent) >= settings.email_code_daily_max:
        raise TooManyRequests("今日获取次数已达上限")

    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(
        EmailCode(
            id=str(uuid4()),
            email=email,
            purpose=purpose,
            code_hash=_hash(email, code),
            expires_at=now + timedelta(minutes=settings.email_code_ttl_minutes),
            sent_ip=ip,
            created_at=now,
        )
    )
    db.commit()
    return code


def verify(db: Session, email: str, purpose: str, code: str) -> None:
    """校验并消费最近一条未使用的码；失败抛 InvalidCode。"""
    now = datetime.now(timezone.utc)
    row = db.execute(
        select(EmailCode)
        .where(
            EmailCode.email == email,
            EmailCode.purpose == purpose,
            EmailCode.used_at.is_(None),
        )
        .order_by(EmailCode.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if row is None or as_utc(row.expires_at) <= now:
        raise InvalidCode("验证码无效或已过期")
    if row.attempts >= settings.email_code_max_attempts:
        raise InvalidCode("验证码错误次数过多，请重新获取")

    if not secrets.compare_digest(row.code_hash, _hash(email, code.strip())):
        row.attempts += 1
        db.commit()
        raise InvalidCode("验证码无效或已过期")

    # 一次性使用：成功即作废，防止同一条码被重复提交
    row.used_at = now
    db.commit()