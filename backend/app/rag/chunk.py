"""父子分块：parent 给模型上下文，child 用于检索。"""

from dataclasses import dataclass
from hashlib import sha256
import re

import jieba

from ..config import settings
from .parse import ParsedBlock

# 子块之间保留少量上下文，避免一句话被切断后完全失去主语
CHILD_OVERLAP = 80
_SENTENCE = re.compile(r"(?<=[。！？!?；;.!?])\s*|\n+")


@dataclass(frozen=True)
class ChunkSpec:
    text: str
    kind: str          # parent | child
    index: int         # 全文内稳定顺序
    parent_index: int | None
    page: int | None
    heading_path: str
    search_text: str
    token_count: int
    content_hash: str


def token_count(text: str) -> int:
    """粗略估算 token：中文按 1 字，其它字符按 4 字符。"""
    if not text:
        return 0
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return cjk + max(0, len(text) - cjk) // 4 + 1


def _split_text(text: str, limit: int, overlap: int = 0) -> list[str]:
    """按句号/换行切分，再拼接到不超过 limit 的块。"""
    parts = [part.strip() for part in _SENTENCE.split(text) if part.strip()]
    chunks: list[str] = []
    buf = ""
    for part in parts:
        # 超长单句硬切，避免一个块永远超过上限
        while len(part) > limit:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.append(part[:limit])
            part = part[limit - overlap :] if overlap else part[limit:]
        if len(buf) + len(part) <= limit:
            buf += part
        else:
            if buf:
                chunks.append(buf)
            buf = part
    if buf:
        chunks.append(buf)
    return chunks


def _search_text(heading_path: str, text: str) -> str:
    # 标题重复写入，提升章节词在 BM25/tsvector 中的权重
    source = f"{heading_path}\n{text}" if heading_path else text
    return " ".join(jieba.cut_for_search(source))


def chunk_blocks(
    blocks: list[ParsedBlock],
    parent_chars: int | None = None,
    child_chars: int | None = None,
) -> list[ChunkSpec]:
    """把解析块变成 parent/child 两层；child.parent_index 指向 parent.index。"""
    parent_chars = parent_chars or settings.rag_parent_chars
    child_chars = child_chars or settings.rag_child_chars
    specs: list[ChunkSpec] = []
    index = 0

    for block in blocks:
        for parent_text in _split_text(block.text, parent_chars):
            parent_index = index
            specs.append(
                ChunkSpec(
                    text=parent_text,
                    kind="parent",
                    index=index,
                    parent_index=None,
                    page=block.page,
                    heading_path=block.heading_path,
                    search_text="",
                    token_count=token_count(parent_text),
                    content_hash=sha256(parent_text.encode("utf-8")).hexdigest(),
                )
            )
            index += 1

            for child_text in _split_text(parent_text, child_chars, CHILD_OVERLAP):
                specs.append(
                    ChunkSpec(
                        text=child_text,
                        kind="child",
                        index=index,
                        parent_index=parent_index,
                        page=block.page,
                        heading_path=block.heading_path,
                        search_text=_search_text(block.heading_path, child_text),
                        token_count=token_count(child_text),
                        content_hash=sha256(child_text.encode("utf-8")).hexdigest(),
                    )
                )
                index += 1
    return specs
