"""一轮对话结束后的收尾：落库、标记状态、投递记忆任务、调度历史压缩。

抽成独立模块的原因：这些动作都是「聊天已经结束之后」的旁路工作，
失败不能影响已经返回给用户的内容，因此统一包在容错里。
"""

import logging
import re

from ..config import settings
from ..roles import Role
from .history import finish_run, save_transcript
from .history_compaction import schedule_compaction
from .memory import enqueue_memory_job, memory_enabled_for
from .quota import rounds_used

logger = logging.getLogger(__name__)

# 用户在这句话里明确要求记住，给提取任务更高优先级
_EXPLICIT_MEMORY = re.compile(r"记住|记一下|别忘|以后都|remember", re.IGNORECASE)


def finalize_run(
    *,
    run_id: str | None,
    status: str,
    owner_key: str,
    user_id: str | None,
    role: str,
    conversation_id: str | None,
    message: str,
    transcript: list[dict] | None = None,
) -> None:
    """把本轮结果落库并触发后续任务；任何一步失败都只记日志。

    transcript 为 None 或空（还没进 runtime 就失败/取消）时，
    至少把用户问题留下，下一轮照样能回放。
    """
    if not run_id:
        return

    saved = list(transcript or [])
    if not saved:
        saved = [{"role": "user", "content": message}]
    save_transcript(run_id, saved)
    finish_run(run_id, status)

    if status != "done" or not conversation_id:
        return

    # 记忆提取只登记任务，绝不阻塞本轮回答；失败也不影响聊天。
    # 所有登录角色（Role 枚举中的 member/admin/superadmin）都登记；
    # 访客需达到最低轮次才提取。
    guest_ready = role == Role.GUEST and rounds_used(owner_key) >= settings.guest_memory_min_rounds
    if role != Role.GUEST or guest_ready:
        try:
            if memory_enabled_for(owner_key):
                enqueue_memory_job(
                    owner_key=owner_key,
                    run_id=run_id,
                    conversation_id=conversation_id,
                    priority=10 if _EXPLICIT_MEMORY.search(message) else 0,
                )
        except Exception:
            logger.exception("enqueue memory job failed: run=%s", run_id)

    schedule_compaction(conversation_id, owner_key)