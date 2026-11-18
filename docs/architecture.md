# 归一 · 架构说明

> 当前是骨架；数据流与模块边界已定，业务逻辑按 TODO 填充。

## 请求链路

```
Browser
  → Caddy（TLS / 限流 / SSE flush）
  → FastAPI（auth / chat / documents / skills / admin / mcp）
  → 队列（全局 8 / 每个用户或访客 1 / 60s）
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
| `models.py` | 数据表；PostgreSQL（timestamptz / 索引） |

## 两个入口

- **浏览器**：`/api/chat` → SSE
- **MCP**：`python -m app.mcp_server`（stdio）；`/mcp`（Streamable HTTP，待实现）

## 数据

- PostgreSQL：compose 内 `db:5432`（本地开发直连 `127.0.0.1:5432`）
- 文件：`/data/uploads`、`artifacts`、`skills`、`indexes`
- 访客身份：`guest_sessions`（30 天滑动续期，`guest_id` 走 HttpOnly Cookie）
- 会话层级：`conversations`（会话元信息 / 标题 / `owner_key`）→ `runs`（每轮执行）→ `messages`（消息）
- 访问记录：`visits`（进入 / 离开时间、停留时长、IP、UA 解析出的设备 / OS / 浏览器、屏幕、时区、来源页），供后续用户画像使用
- 临时文档 7 天；收藏后转 personal

## 待实现

1. `api/auth.py`：密码登录与 JWT（访客会话已落库）
2. `agent/runtime.py`：ReAct + 工具调用
3. `rag/retrieve.py`：BM25 + hnswlib + RRF + rerank
4. `api/documents.py`：上传后异步索引
5. `api/admin.py`：配额、审计、run 回放
6. `mcp_server.py`：只读工具 + HTTP 挂载
