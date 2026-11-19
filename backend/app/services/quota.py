"""配额计算：访客免费体验轮次。

口径：一轮 = 一次「提问 → 回答结束」，即 chat 接口通过并发闸后创建的 1 条 run。
按 run 表计数而不是额外加计数字段：run 是每轮的事实记录，不会漂移；
访客上限 20 轮、最多 20 条数据，走索引即可，无需缓存。
"""

from sqlalchemy import func, select

from ..db import SessionLocal
from ..models import Conversation, Run


def rounds_used(owner_key: str) -> int:
    """该身份已消耗的对话轮数（含失败/中断的轮次——用了就算）。"""
    db = SessionLocal()
    try:
        stmt = (
            select(func.count(Run.id))
            .join(Conversation, Run.conversation_id == Conversation.id)
            .where(Conversation.owner_key == owner_key)
        )
        return int(db.execute(stmt).scalar_one())
    finally:
        db.close()