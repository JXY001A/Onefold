"""上下文预算与组装（骨架）。"""

from dataclasses import dataclass

from ..config import settings


@dataclass
class ContextBudget:
    system: int = settings.context_system
    tools: int = settings.context_tools
    memory: int = settings.context_memory
    rag: int = settings.context_rag
    history: int = settings.context_history
    output: int = settings.context_output


def build_messages(
    query: str,
    history: list[dict] | None = None,
    rag_chunks: list[dict] | None = None,
    skill_text: str | None = None,
) -> list[dict]:
    """组上下文：system + skill + memory + RAG + 最近对话 + 当前问题。

    TODO:
    - 按 ContextBudget 裁剪；超预算先摘要旧对话
    - RAG 片段带引用（文档名/页码）
    - memory 从用户画像/长期摘要读取
    """
    system = "你是归一（Onefold），一个基于证据回答问题的研究助手。"
    if skill_text:
        system += f"\n\n[当前 Skill]\n{skill_text}"

    messages: list[dict] = [{"role": "system", "content": system}]

    if rag_chunks:
        refs = "\n\n".join(
            f"[{c.get('filename', 'doc')} p.{c.get('page', '?')}] {c.get('text', '')}"
            for c in rag_chunks
        )
        messages.append({"role": "system", "content": f"[参考资料]\n{refs}"})

    if history:
        messages.extend(history[-20:])

    messages.append({"role": "user", "content": query})
    return messages
