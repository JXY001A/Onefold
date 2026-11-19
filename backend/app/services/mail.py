"""发信：SMTP 未配置时进入 dev 模式（写日志），配置后自动真实发送。

为什么用标准库 smtplib：只发纯文本验证码，不值得为它引入第三方依赖。
调用方必须用同步 def 端点（FastAPI 会放进线程池），避免阻塞事件循环。
"""

import logging
import smtplib
from email.message import EmailMessage

from ..config import settings

log = logging.getLogger("onefold.mail")

_SUBJECTS = {
    "register": "归一 · 注册验证码",
    "reset": "归一 · 重置密码验证码",
}


def dev_mode() -> bool:
    """smtp_host 为空即视为本地开发：不发信，只把验证码写日志。"""
    return not settings.smtp_host


def send_code(to: str, code: str, purpose: str) -> None:
    """发送验证码邮件；SMTP 失败会抛出异常，由调用方转成 502。"""
    ttl = settings.email_code_ttl_minutes
    text = (
        f"你的验证码是 {code}，{ttl} 分钟内有效，仅可使用一次。\n"
        "如果这不是你本人的操作，请忽略这封邮件。"
    )

    if dev_mode():
        log.warning("[dev 模式] 未配置 SMTP，验证码 %s（%s）→ %s", code, purpose, to)
        return

    msg = EmailMessage()
    msg["Subject"] = _SUBJECTS.get(purpose, "归一 · 验证码")
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to
    msg.set_content(text)

    if settings.smtp_ssl:
        server: smtplib.SMTP = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10)
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
    try:
        if not settings.smtp_ssl:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
    finally:
        server.quit()