"""测试环境固定值。

必须在导入 app 之前生效（pytest 会先加载 conftest）：
环境变量优先级高于 .env 文件，因此这里能压住本地 .env 里的生产配置，
避免测试真发邮件、以及 Secure Cookie 在 http 下不被回传导致身份丢失。
"""

import os

os.environ["ENV"] = "dev"
os.environ["SMTP_HOST"] = ""
os.environ["COOKIE_SECURE"] = "false"


def cleanup_owner(owner_key: str) -> None:
    """清掉某个 owner（user:/guest:）名下的全部记忆数据。

    记忆相关测试共用：用例结束必须还原库，否则残留会污染快照与统计。
    """
    from sqlalchemy import delete

    from app.db import SessionLocal
    from app.models import MemoryEvent, MemoryItem, MemoryJob, MemorySetting

    with SessionLocal() as db:
        db.execute(delete(MemoryEvent).where(MemoryEvent.owner_key == owner_key))
        db.execute(delete(MemoryItem).where(MemoryItem.owner_key == owner_key))
        db.execute(delete(MemoryJob).where(MemoryJob.owner_key == owner_key))
        db.execute(delete(MemorySetting).where(MemorySetting.owner_key == owner_key))
        db.commit()