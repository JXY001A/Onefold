"""文档解析：把 PDF / Markdown / DOCX / TXT 变成统一文本块。

解析结果只保留「文本 + 页码 + 标题路径」，不在这里做分块或 embedding。
扫描 PDF 不做 OCR，直接抛 UnsupportedDocument，让任务进入失败重试。
"""

from dataclasses import dataclass
from pathlib import Path
import re

import pypdf
from docx import Document as DocxDocument


class UnsupportedDocument(ValueError):
    """文件类型不支持，或扫描件无法提取文本。"""


@dataclass(frozen=True)
class ParsedBlock:
    text: str
    page: int | None = None
    heading_path: str = ""


def _clean(text: str) -> str:
    # 保留段落边界，只压缩行内空白和连续空行
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _markdown_blocks(text: str) -> list[ParsedBlock]:
    """按 Markdown 标题切块，并维护 heading_path。"""
    blocks: list[ParsedBlock] = []
    heading_stack: list[str] = []
    buffer: list[str] = []
    in_code = False

    def flush() -> None:
        content = _clean("\n".join(buffer))
        if content:
            blocks.append(ParsedBlock(content, heading_path=" / ".join(heading_stack)))
        buffer.clear()
    # 按行切分
    for line in text.splitlines():
        # 代码块里的 # 不是标题，必须跳过
        if line.strip().startswith("```"):
            in_code = not in_code
            buffer.append(line)
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line) if not in_code else None
        if match:
            flush()
            # 标题级别 = # 的数量
            level = len(match.group(1))
            # heading_stack 里始终只放「当前标题的祖先链」：
            # 相当于： del heading_stack[level - 1:]  heading_stack.append(title) # 砍掉第 level 个及之后， 压入当前标题
            heading_stack[level - 1 :] = [match.group(2).strip()]
        else:
            buffer.append(line)
    flush()
    return blocks


def _plain_blocks(text: str) -> list[ParsedBlock]:
    """TXT 按空行分段；没有标题时 heading_path 为空。"""
    blocks = []
    for para in re.split(r"\n\s*\n", text):
        content = _clean(para)
        if content:
            blocks.append(ParsedBlock(content))
    return blocks


def _pdf_blocks(path: Path) -> list[ParsedBlock]:
    """PDF 按页提取；页码从 1 开始。"""
    try:
        reader = pypdf.PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise UnsupportedDocument(f"PDF 解析失败：{type(exc).__name__}") from exc

    blocks: list[ParsedBlock] = []
    for index, text in enumerate(pages, 1):
        # 按空行分段
        for para in re.split(r"\n\s*\n", text):
            content = _clean(para)
            if content:
                blocks.append(ParsedBlock(content, page=index))
    if not blocks:
        raise UnsupportedDocument("PDF 没有可提取文本，可能是扫描件")
    return blocks


def _docx_blocks(path: Path) -> list[ParsedBlock]:
    """DOCX 按段落；标题样式写入 heading_path。"""
    try:
        document = DocxDocument(str(path))
    except Exception as exc:
        raise UnsupportedDocument(f"DOCX 解析失败：{type(exc).__name__}") from exc

    blocks: list[ParsedBlock] = []
    stack: list[str] = []
    for para in document.paragraphs:
        text = _clean(para.text)
        if not text:
            continue
        style = (para.style.name or "") if para.style else ""
        if style.lower().startswith("heading"):
            level_match = re.search(r"(\d+)", style)
            level = int(level_match.group(1)) if level_match else 1
            stack[level - 1 :] = [text]
        else:
            blocks.append(ParsedBlock(text, heading_path=" / ".join(stack)))
    if not blocks:
        raise UnsupportedDocument("DOCX 没有可提取文本")
    return blocks


def parse_document(path: str, filename: str | None = None) -> list[ParsedBlock]:
    """按扩展名分派解析器；不支持的类型直接失败。"""
    file_path = Path(path)
    suffix = Path(filename or file_path.name).suffix.lower()
    if suffix == ".pdf":
        return _pdf_blocks(file_path)
    if suffix == ".docx":
        return _docx_blocks(file_path)
    if suffix in (".md", ".markdown"):
        return _markdown_blocks(file_path.read_text(encoding="utf-8", errors="replace"))
    if suffix == ".txt":
        return _plain_blocks(file_path.read_text(encoding="utf-8", errors="replace"))
    raise UnsupportedDocument(f"不支持的文件类型：{suffix or '未知'}")
