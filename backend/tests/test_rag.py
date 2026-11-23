"""RAG 基础组件测试：解析、分块、BM25、RRF 与失败回退。"""

from pathlib import Path

from app.config import settings
from app.rag import embed as rag_embed
from app.rag.bm25 import bm25_rank
from app.rag.chunk import chunk_blocks
from app.rag.parse import parse_document
from app.rag.rrf import rrf_fuse
import app.rag.retrieve as rag_retrieve


def test_markdown_parse_keeps_heading_path(tmp_path: Path):
    path = tmp_path / "design.md"
    path.write_text("# Onefold\n\n## 数据模型\n\n用户和会话分开保存。\n", encoding="utf-8")

    blocks = parse_document(str(path), path.name)

    assert blocks
    assert blocks[-1].heading_path == "Onefold / 数据模型"
    assert "用户和会话" in blocks[-1].text


def test_chunk_blocks_builds_parent_child(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text("第一段介绍数据库。第二段介绍检索。第三段介绍缓存。", encoding="utf-8")
    blocks = parse_document(str(path), path.name)

    specs = chunk_blocks(blocks, parent_chars=20, child_chars=10)

    parents = [spec for spec in specs if spec.kind == "parent"]
    children = [spec for spec in specs if spec.kind == "child"]
    assert parents and children
    assert all(child.parent_index in {parent.index for parent in parents} for child in children)
    # 中文分词结果应包含可检索词，而不是原始整句
    assert any("数据库" in child.search_text for child in children)


def test_bm25_rank_prefers_relevant_document():
    docs = [
        "Onefold 从 SQLite 迁移到 PostgreSQL，为了 pgvector 和并发写入。",
        "Onefold 前端使用 React 和 Vite。",
        "今天杭州天气多云。",
    ]

    ranked = bm25_rank("为什么迁移 PostgreSQL", docs, top_n=3)

    assert ranked
    assert ranked[0][0] == 0


def test_rrf_fuse_prefers_document_hit_by_both_lists():
    fused = rrf_fuse([["a", "b"], ["b", "c"]], k=60)

    assert fused[0][0] == "b"
    assert dict(fused)["b"] > dict(fused)["a"]


def test_bm25_rank_handles_empty_input():
    assert bm25_rank("", ["a"], 3) == []
    assert bm25_rank("query", [], 3) == []


def test_embed_falls_back_to_openrouter(monkeypatch):
    calls: list[str] = []

    def fake_request(batch, url, attempts):
        calls.append(url)
        if len(calls) == 1:
            raise rag_embed.EmbeddingError("primary down")
        return [[0.0] * settings.embed_dim for _ in batch]

    monkeypatch.setattr(rag_embed, "_request", fake_request)
    monkeypatch.setattr(settings, "embed_base_url", "http://primary.invalid")
    vectors = rag_embed.embed_texts(["测试"])

    assert len(vectors) == 1
    assert len(vectors[0]) == settings.embed_dim
    assert calls[0] != calls[1]
    assert "openrouter.ai" in calls[1]


def test_retrieve_returns_empty_when_retrieval_fails(monkeypatch):
    def broken(*_args, **_kwargs):
        raise RuntimeError("schema not migrated")

    monkeypatch.setattr(rag_retrieve, "lexical_candidates", broken)
    result = rag_retrieve.retrieve("问题", "user:test", db=object())
    assert result == []
