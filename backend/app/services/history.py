"""会话存取的公开入口。

数据层级：
    conversations（会话：标题 / 归属 / 活跃时间）
        └── runs（每轮执行：状态 / 耗时 / token）
                └── messages（消息：角色 / 内容）

归属统一用 owner_key（格式与 Principal.lock_key 一致）：
    user:<user_id>    登录用户
    guest:<guest_id>  匿名访客

实现按职责拆在同目录的模块里，这里只做统一导出：
    conversation_store  会话元信息
    message_reader      前端渲染用的消息读取
    history_context     给 LLM 的上下文组装
    history_replay      消息行还原成 OpenAI 形状
    history_summary     摘要输入与 token 估算
    history_compaction  压缩判定与落库
    run_store           轮次与消息落库
"""

from .conversation_store import (
    TITLE_MAX,
    conversation_owned_by,
    get_or_create_conversation,
    list_conversations,
)
from .history_compaction import maybe_compact_history
from .history_context import SUMMARY_KEEP, load_history
from .history_summary import estimate_tokens
from .message_reader import load_conversation_messages
from .run_store import create_run, finish_run, save_transcript

__all__ = [
    "SUMMARY_KEEP",
    "TITLE_MAX",
    "conversation_owned_by",
    "create_run",
    "estimate_tokens",
    "finish_run",
    "get_or_create_conversation",
    "list_conversations",
    "load_conversation_messages",
    "load_history",
    "maybe_compact_history",
    "save_transcript",
]