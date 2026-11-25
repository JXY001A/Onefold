"""数据表。字段与 docs/architecture.md 的数据模型保持一致。

按业务域分文件，这里统一导出，调用方仍然只写 `from ..models import X`：

    account   用户、验证码、访客、访问记录、用量、审计
    chat      会话、轮次、消息、工具审计、历史摘要
    document  文档、切片、产物、解析队列、技能包
    memory    记忆开关、记忆本体、提取队列、变更审计
"""

from .account import AuditLog, EmailCode, GuestSession, UsageDaily, User, Visit
from .chat import Conversation, ConversationSummary, Message, Run, ToolCall
from .common import Base, as_utc, now
from .document import Artifact, Chunk, Document, DocumentJob, KnowledgeBase, Skill
from .memory import MemoryEvent, MemoryItem, MemoryJob, MemorySetting

__all__ = [
    "Artifact",
    "AuditLog",
    "Base",
    "Chunk",
    "Conversation",
    "ConversationSummary",
    "Document",
    "DocumentJob",
    "EmailCode",
    "KnowledgeBase",
    "GuestSession",
    "MemoryEvent",
    "MemoryItem",
    "MemoryJob",
    "MemorySetting",
    "Message",
    "Run",
    "Skill",
    "ToolCall",
    "UsageDaily",
    "User",
    "Visit",
    "as_utc",
    "now",
]