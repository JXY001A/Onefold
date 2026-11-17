# 归一 · 架构说明

> 当前是骨架；数据流与模块边界已定，业务逻辑按 TODO 填充。

## 请求链路

```
Browser
  → Caddy（TLS / 限流 / SSE flush）
  → FastAPI（auth / chat / documents / skills / admin / mcp）
  → 队列（全局 8 / 每人 1 / 60s）
  → Agent Runtime（context + ReAct + tools）
  → RAG / Skill / MCP / DeepSeek
  → SSE 返回 → 写 usage/audit
```

## 模块边界

| 模块 | 职责 |
|---|---|
| `api/` | HTTP 契约；不写业务 |
| `agent/` | 上下文预算、ReAct 循环、工具路由 |
| `rag/` | 分块、嵌入、索引、检索、重排 |
| `services/` | LLM / embeddings / search 的供应商适配 |
| `workers/` | 队列、清理任务 |
| `mcp_server.py` | MCP stdio 入口；HTTP 后续挂载 |
| `models.py` | 数据表；SQLite WAL |

## 两个入口

- **浏览器**：`/api/chat` → SSE
- **MCP**：`python -m app.mcp_server`（stdio）；`/mcp`（Streamable HTTP，待实现）

## 数据

- SQLite：`/data/onefold.db`
- 文件：`/data/uploads`、`artifacts`、`skills`、`indexes`
- 临时文档 7 天；收藏后转 personal

## 待实现

1. `api/auth.py`：密码/JWT/访客 session
2. `agent/runtime.py`：ReAct + 工具调用
3. `rag/retrieve.py`：BM25 + hnswlib + RRF + rerank
4. `api/documents.py`：上传后异步索引
5. `api/admin.py`：配额、审计、run 回放
6. `mcp_server.py`：只读工具 + HTTP 挂载
