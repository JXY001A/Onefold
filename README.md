# 归一 · Onefold

> 万般能力，归一入口。一个云端 Agent 助手：研究检索、临时文档问答、Skill 按需加载、MCP 工具调用、流式回答。
>
> 当前状态：**架构骨架**。可运行的健康检查 + SSE 占位 + 前端聊天壳，业务逻辑按 TODO 填充。

## 技术栈

- 前端：React 19 + TypeScript + Vite + Tailwind + shadcn/ui（组件按需加）
- 后端：Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2 + SQLite(WAL)
- Agent：自写 ReAct 循环 + OpenAI SDK（DeepSeek 兼容端点）
- RAG：jieba + rank_bm25 + hnswlib + bge-m3/reranker（4080 Infinity）
- MCP：`mcp>=2`，同一服务双传输（stdio / Streamable HTTP）
- 部署：Docker + Caddy + GitHub Actions + 阿里云 ACR

## 目录

```
onefold/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── config.py           # 环境配置
│   │   ├── db.py               # SQLite + SQLAlchemy
│   │   ├── models.py           # 数据表
│   │   ├── api/                # auth / chat / documents / skills / admin / mcp
│   │   ├── agent/              # ReAct 循环 + 上下文预算
│   │   ├── rag/                # 分块 / 嵌入 / 索引 / 检索 / 重排
│   │   ├── services/           # LLM / embeddings / search
│   │   ├── workers/            # 队列 / 清理
│   │   └── mcp_server.py       # MCP 服务入口（stdio）
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/pages/              # Landing / Chat / Documents / Skills / Admin
│   ├── src/lib/sse.ts          # SSE 解析 + streamChat
│   └── package.json
├── Dockerfile
├── docker-compose.yml
├── Caddyfile
├── deploy.sh
└── .github/workflows/deploy.yml
```

## 本地运行

### 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# 打开 http://127.0.0.1:8000/healthz
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 打开 http://127.0.0.1:5173
```

### MCP（stdio）

```bash
cd backend
python -m app.mcp_server
```

## Docker

```bash
cp .env.example .env
docker compose up --build
# 打开 http://localhost
```

## 下一步（按优先级）

1. 实现 `api/auth.py`：申请码、登录、访客、JWT
2. 实现 `agent/runtime.py`：ReAct + DeepSeek 工具调用
3. 实现 `rag/retrieve.py`：分块、bge-m3、hnswlib、RRF、rerank
4. 实现 `api/documents.py`：上传、索引、收藏
5. 实现 `api/admin.py`：审批、配额、用量、run 回放
6. 补齐 `mcp_server.py` 的工具与 `/mcp` HTTP 挂载

设计文档见 `docs/architecture.md`。
