"""长期记忆服务的公开入口。

实现按职责拆在同目录的 memory_* 模块里，这里只做统一导出：
API、worker、agent 三方都依赖本模块，不需要感知内部如何拆分。

    memory_categories  分类定义与归一
    memory_scope       owner_key 解析与开关
    memory_jobs        提取队列（入队/抢占/重试）
    memory_evidence    交给提取器的对话证据
    memory_store       写入与审计、序列化
    memory_admin       列表、编辑、删除、清空
    memory_scoring     打分
    memory_context     按预算挑选并渲染注入文本
"""

from .memory_admin import (
    clear_memory,
    delete_memory_item,
    list_memory,
    update_memory_item,
)
from .memory_categories import CATEGORIES, CATEGORY_ALIASES, normalize_category
from .memory_context import (
    get_memory_snapshot,
    invalidate_memory_snapshots,
    load_memory_context,
)
from .memory_evidence import message_is_user_evidence, run_turns
from .memory_jobs import (
    claim_memory_job,
    enqueue_memory_job,
    fail_memory_job,
    finish_memory_job,
    requeue_stale_jobs,
)
from .memory_scope import memory_enabled_for, owner_kind, set_memory_enabled
from .memory_store import apply_extraction

__all__ = [
    "CATEGORIES",
    "CATEGORY_ALIASES",
    "apply_extraction",
    "claim_memory_job",
    "clear_memory",
    "delete_memory_item",
    "enqueue_memory_job",
    "fail_memory_job",
    "finish_memory_job",
    "get_memory_snapshot",
    "invalidate_memory_snapshots",
    "list_memory",
    "load_memory_context",
    "memory_enabled_for",
    "message_is_user_evidence",
    "normalize_category",
    "owner_kind",
    "requeue_stale_jobs",
    "run_turns",
    "set_memory_enabled",
    "update_memory_item",
]