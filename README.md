# 归一 · Onefold

> 万般能力，归一入口。一个云端 Agent 助手：研究检索、临时文档问答、Skill 按需加载、MCP 工具调用、流式回答。
>
> 当前状态：**架构骨架**。可运行的健康检查 + SSE 占位 + 前端聊天壳，业务逻辑按 TODO 填充。

## 技术栈

- 前端：React 19 + TypeScript + Vite + Tailwind + shadcn/ui（组件按需加）
- 后端：Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2 + PostgreSQL 16
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
│   │   ├── db.py               # 数据库连接（PostgreSQL）
│   │   ├── models.py           # 数据表
│   │   ├── api/                # auth / chat / conversations / documents / skills / admin / mcp
│   │   ├── agent/              # ReAct 循环 + 上下文预算 + 工具注册表
│   │   ├── rag/                # 分块 / 嵌入 / 索引 / 检索 / 重排
│   │   ├── services/           # LLM / embeddings / 联网搜索（tools/）/ 邮件 / 配额
│   │   ├── workers/            # 队列 / 清理
│   │   └── mcp_server.py       # MCP 服务入口（stdio）
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/pages/              # Landing / Chat / Documents / Skills / Admin
│   ├── src/lib/sse.ts          # SSE 解析 + streamChat
│   ├── src/lib/chat.ts         # 会话/消息拉取 + 工具行折叠
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

生产部署（GitHub Actions + 阿里云 ACR + Caddy 自动 HTTPS）见 [docs/deploy.md](docs/deploy.md)；想看从创建 ACR 到上线的完整流程、原理与踩坑记录，见 [docs/deploy-walkthrough.md](docs/deploy-walkthrough.md)。

## 账号与配额

| 角色 | 来源 | 能力 |
|---|---|---|
| 游客 | 打开页面自动获得（HttpOnly Cookie，30 天滑动续期） | 直接可用，累计 20 轮免费；用完引导注册 |
| 成员 member | 邮箱 + 验证码注册 | 聊天不限轮次 |
| 管理员 admin | 超管在后台指定 | 可见后台：审批、用户列表、用量 |
| 超管 superadmin | 手动写库 | 可改角色、停用账号（变更写 `audit_logs`） |

### 邮箱注册与找回密码

- 注册：填邮箱 → 收 6 位验证码 → 填验证码与密码（昵称可留空，默认取 `@` 前部分并自动去重）
- 找回密码：同样走邮箱验证码，改密后 `password_changed_at` 更新，此前签发的 Cookie 立即失效
- 验证码只存 `sha256(email + code + secret)`，10 分钟有效、60 秒冷却、每小时 5 封 / 每天 10 封、错 5 次作废、用过作废
- `SMTP_HOST` 为空 = dev 模式：验证码只写后端日志，并在接口响应里回 `dev_code`，本地不用配邮箱；配好 `.env` 里的 SMTP 后自动真实发信，代码不用改
- 早期没有邮箱的账号（如手动写入的超管）仍可用用户名登录

超管写入示例（密码哈希用 argon2，不要手写明文；`email` 留空则只能用用户名登录）：

```bash
cd backend
python - <<'PY'
from passlib.context import CryptContext
from sqlalchemy import text
from app.db import SessionLocal

db = SessionLocal()
db.execute(
    text("INSERT INTO users (id, username, email, password_hash, role, status, created_at) "
         "VALUES (gen_random_uuid()::text, 'your-name', :e, :h, 'superadmin', 'active', now())"),
    {"e": "you@example.com", "h": CryptContext(schemes=["argon2"]).hash("your-password")},
)
db.commit()
db.close()
PY
```

## 模型与工具

模型走 DeepSeek 的 OpenAI 兼容接口，工具是标准 function calling（不是 MCP：MCP 留给后续「接外部服务」用）。

| 配置项 | 默认 | 说明 |
|---|---|---|
| `MODEL` | `deepseek-flash` | 聊天模型 |
| `SEARCH_ENABLED` | `true` | `false` 即不注册任何工具，行为回到未接入状态 |
| `SEARCH_COUNT` / `SEARCH_MIN_SCORE` | `5` / `1.0` | 搜索条数 / 相关度阈值 |
| `FETCH_MAX_CHARS` | `6000` | 抓取正文截断长度 |
| `AGENT_MAX_STEPS` | `6` | 单轮最多几轮工具循环，最后一步强制收尾 |
| `AGENT_TOOL_TIMEOUT_S` | `15` | 单个工具执行超时 |
| `CONTEXT_FULL_RUNS` | `2` | 最近几轮对话完整回放（含工具正文） |
| `CONTEXT_TOOL_RESULT` | `6000` | 回放时工具正文的总字符预算 |

当前工具：`web_search`（DeepSeek `/v1/tools/search`）、`fetch_url`（`/v1/tools/fetch`）。

- **防提示注入**：网页内容一律包在 `<external_content source="URL">…</external_content>` 里再交给模型，正文中的同名标签字面量被转义，无法提前闭合逃逸；`fetch_url` 只允许公网 http/https，拒私网/回环/`file:`
- **工具调用落表**：`messages` 表存完整的 assistant(tool_calls) + tool 行（含网页正文，供下轮回放），`tool_calls` 表存审计摘要（参数/耗时/成败/结果前 200 字）与 `data_json`（搜索命中的标题/链接/站点/日期/简介）
- **界面呈现**：工具痕迹收在气泡右上角胶囊（「正在搜索… / 搜索到 N 个网页」），点开右侧抽屉列出每条结果的站点、日期、标题与简介，标题可直接跳转原文
- **历史回放**：最近 `CONTEXT_FULL_RUNS` 轮完整回放，更早的降级成 `[历史检索摘要]`；超预算时从最旧的一整组开始省略（整组裁，不切碎配对）

## 下一步（按优先级）

1. 实现 `rag/retrieve.py`：分块、bge-m3、hnswlib、RRF、rerank
2. 实现 `api/documents.py`：上传、索引、收藏（上传暂未对外暴露）
3. 后台补齐：run 回放、访客画像报表、每日配额（登录用户）
4. 补齐 `mcp_server.py` 的工具与 `/mcp` HTTP 挂载
5. 代码执行等新工具：`agent/tools.py` 加一条 schema + `execute()` 加一个分支

设计文档见 `docs/architecture.md`。
