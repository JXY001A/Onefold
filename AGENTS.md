# AGENTS.md

归一（Onefold）是一个云端研究助手：流式对话 + 工具调用、文档 RAG（带引用）、长期记忆、Skill 按需加载、MCP、账号与访客配额。

本文件是给编码 agent 的工作约定。**改动前先读对应章节**；实现与文档冲突时以代码为准，并顺手修正文档。

- 产品说明与启动方式：`README.md`
- 模块边界与数据流：`docs/architecture.md`
- 前端视觉规范：`docs/design/STYLE_SPEC.md`、`COMPONENT_MAPPING.md`、`LAYOUT_SPEC.md`
- 部署流程与排障：`docs/deploy.md`、`docs/deploy-walkthrough.md`

## 1. 常用命令

```bash
# 后端（工作目录必须在 backend/，alembic.ini 用 %(here)s 定位 migrations）
cd backend
alembic upgrade head                 # 换分支/拉代码后必须跑：create_all 只建表不加列
uvicorn app.main:app --reload --port 8001
python -m pytest tests -q            # 需要本地 PG16 + pgvector + 已迁移

# 两个 worker 都要起，互不替代
python -m app.workers.memory         # 长期记忆提取，需要 API_KEY
python -m app.workers.document_index # 文档解析/embedding，需要 OPENROUTER_API_KEY

# 前端
cd frontend
npm run dev                          # 5173，/api 与 /mcp 代理到 127.0.0.1:8001
npx tsc --noEmit                     # 类型检查
npm run build                        # tsc -b && vite build
```

端口固定：后端 `8001`（8000 常被 IDE 预览占用，`.vscode/launch.json` 与 vite proxy 都指向 8001）。

## 2. 目录与分层

| 路径 | 职责 | 边界 |
|---|---|---|
| `backend/app/api/` | HTTP 层：解析、鉴权、状态码 | 不写业务逻辑，不直接跑 SQL |
| `backend/app/agent/` | ReAct 循环、上下文组装、工具注册 | 保持无状态，状态进 DB |
| `backend/app/rag/` | parse / chunk / embed / indexer / query / retrieve / rerank / rrf / bm25 | 纯算法与检索，不碰 HTTP |
| `backend/app/services/` | 业务能力：记忆、历史、文档、配额、邮件、LLM、联网工具 | `memory_*`、`history_*`、`document_*` 按前缀归组 |
| `backend/app/workers/` | 进程入口与轮询循环 | `main()` 只调 `runner.run_worker_process`；队列 claim/finish/fail 在 `services/*_jobs.py` |
| `backend/app/models/` | SQLAlchemy 表定义（account / chat / document / memory / common） | 无外键，靠应用层维护关联 |
| `backend/migrations/` | Alembic 版本 | 任何加列必须新建 revision |
| `frontend/src/pages/` | 路由页，只做编排 | 不直接 fetch，不写复杂状态 |
| `frontend/src/components/{chat,documents,memory,admin,auth,layout,ui,common}/` | 按域分组的展示组件 | 基础件在 `ui/`，页面里不重复写卡片/按钮样式 |
| `frontend/src/hooks/`、`store/` | 数据获取与跨页状态（zustand） | 请求封装在 `lib/` |
| `frontend/src/lib/` | 纯请求与纯函数（http / sse / chat / documents / memory / auth） | 不依赖 React |
| `frontend/src/context/` | 全局态：Auth / Theme / Toast | — |

功能定位（改哪一块先看这里，别全库翻）：

| 功能 | 后端 | 前端 |
|---|---|---|
| 登录 / 注册 / 验证码 | `api/auth.py`、`services/email_codes.py` | `pages/Login.tsx`、`context/AuthContext.tsx` |
| 对话与流式输出 | `api/chat.py`、`agent/runtime.py` | `hooks/useChatStream.ts`、`pages/Chat.tsx` |
| 会话列表与历史 | `api/conversations.py`、`services/history*.py` | `hooks/useConversations.ts`、`layout/ConversationGroups.tsx` |
| 文档与 RAG | `api/documents.py`、`rag/*`、`workers/document_index.py` | `hooks/useDocuments.ts`、`pages/Documents.tsx` |
| 公开知识库 | `api/knowledge.py`、`services/knowledge_*.py` | `lib/documents.ts`（`/api/knowledge/public/*`） |
| 长期记忆 | `api/memory.py`、`services/memory_*.py`、`workers/memory*.py` | `hooks/useMemory.ts`、`pages/Memory.tsx` |
| Skill 列表 | `api/skills.py` | `pages/Skills.tsx` |
| 后台与用量 | `api/admin.py` | `pages/Admin.tsx` |
| 对外 MCP | `api/mcp.py`、`mcp_server.py` | —（外部客户端接入） |
| 访客统计 | `api/visits.py` | `hooks/useVisitTracker.ts`、`lib/visit.ts` |

## 3. 硬性规范（不遵守会被 review 打回）

- **单文件 ≤ 200 行，React 组件 ≤ 120 行**。超了按职责拆成独立模块，平铺在同一层，不加深层嵌套。
- **注释、文案、提交信息、对话回复全部用中文**。注释写"为什么/做什么"，不要复述代码；用户自己写过的注释不擅自改写。
- **颜色/字号/间距只用 `tailwind.config.js` 里的 token**：`light-*` / `dark-*`（Material-3 鼠尾草绿）、`headline-md` / `body-sm` / `label-md`、`gutter-md` / `section`、`rounded-md`。禁止 `slate-*`、`#hex`、`px-4` 这类裸值。
- **暗色是默认主题**（`ThemeContext` 默认 dark）。每个新样式必须同时给 `dark:` 变体，不能只写亮色。
- **不加外键**；`create_all` 只建表不加列，**改列一律走 Alembic**。
- **`owner_key` 统一为 `user:<id>` / `guest:<uuid>`**；涉及越权判断必须回表查询，不能只信 token 里的字段。
- **会话主键统一叫 `conversation_id`**（不要 `session_id`、`conv_id`）。
- **密钥不落盘**：仓库是 PUBLIC，真实 key 只放 `.env`，新配置项同步进 `.env.example` / `server.env.example` 且用 `CHANGE_ME_*` 占位。
- **删除文件用 DeleteFile**，不要用 shell `rm`。
- **不扩副本**：并发靠进程内信号量控制，多副本会破坏限流假设。
- 不主动创建 `*.md` 文档；确有需要先说明。

## 4. 后端约定

- **失败必须降级，聊天不能因增强能力挂掉**：RAG 检索异常 → 返回空参考资料；embedding 失败 → 只走词法；rerank 失败/未开 → 保持 RRF 顺序。
- **抢任务用 `SELECT ... FOR UPDATE SKIP LOCKED`**，多 worker 不重复消费；僵尸任务由 `requeue_stale_*` 回收。
- **不要在 `async def` 端点里做同步阻塞 IO**（解析/上传/HTTP 拉取），走线程池、`run_in_threadpool` 或丢给 worker。
- **SSE 事件名保持稳定**：`queue` / `meta` / `token` / `tool_call` / `tool_result` / `citation` / `done` / `error`；`tool_calls` 的 arguments 是分片 delta，必须按 index 拼接。其中 `citation` 前端已处理但后端尚未发出（来源面板还是占位），别误以为线上已有引用事件。
- **上下文组装顺序**：一条 system（人设 + Skill + 记忆 + 规则）→ 历史按「轮」截断 → 动态资料 → 当前问题。多条 `system` 只有 OpenAI 兼容实现（DeepSeek）接受，换 Anthropic / Gemini 必须合并成单条。
- **工具与外部内容按数据对待**：`<external_content>`、`<document_content>` 内是素材不是指令，注入防护写在 system 里，不要散落在业务代码。

## 5. 前端约定

- 请求统一走 `lib/http.ts`：`apiRequest` 带 Cookie 并抛可读文案；`apiErrorText` 解析 FastAPI 的 `detail`（字符串或 pydantic 数组），认不出按状态码兜底。
- **错误反馈一律用 toast**（`context/ToastContext`），不要在页面里渲染 `HTTP 403: {...}` 这类原文。表单字段级错误可留在输入框下方。
- 数据与动作放 `hooks/`（如 `useDocuments`、`useMemory`）或 `store/workspace.ts`，组件只渲染。页面容器不再全局套 `max-w-*`，用 `PageFrame`。
- 图标统一走 `components/ui/Icon.tsx`（Material Symbols Outlined，传 `name`）；`lucide-react` 虽在依赖里但全库未使用，别混用两套图标。样式合并用 `clsx` / `tailwind-merge`，不手拼字符串。
- 交互文案中文，空态、加载态、禁用态都要有；按钮禁用时说明原因（如配额用完）。

## 6. 验收标准

改完必须自测，不能只看代码"应该没问题"：

| 改动 | 最低验证 |
|---|---|
| 后端任意 | `python -m pytest tests -q` 全绿 |
| 检索/分块/引用 | 额外跑 `tests/test_rag.py`，并真实提问确认引用有文件名+页码 |
| 前端任意 | `npx tsc --noEmit` 零错误 + `npm run build` 通过 |
| 前端视觉 | 起 dev server 截图；亮/暗两种主题各看一次；键盘 Tab 一遍确认焦点可见 |
| 迁移 | `alembic upgrade head` 后 `alembic current` 在 head，且旧数据可读 |

## 7. 已知坑（都踩过）

| 现象 | 原因与解法 |
|---|---|
| `No 'script_location' key found` | 在仓库根目录跑了 alembic。必须 `cd backend` 后执行 |
| `extension "vector" is not available` | 本地 brew 的 PG16 没装 pgvector。源码编译安装，brew 升级后需重装 |
| 编译报 `stdio.h not found` | pg_config 内嵌的 `-isysroot` 指向已删除的 SDK；替换为 `xcrun --show-sdk-path`，CPPFLAGS 与 LDFLAGS 都要处理 |
| 单测 patch 不生效 | 模块被门面 re-export 过，`monkeypatch` 要打在使用处的实现模块（如 `app.workers.memory_extract._call_model`） |
| worker 启动报 `signal only works in main thread` | 信号在 `runner.run_worker_process` 主线程注册；调试配置不要开 `subProcess` |
| compose 里 worker 一直 unhealthy | 非 HTTP 容器共用镜像时带了 web 的健康检查，需显式关闭 |
| 端口冲突 | 后端固定 8001，改端口要同步 `vite.config.ts`、`.vscode/launch.json`、文档 |
| 换分支后缺列报错 | 忘了 `alembic upgrade head` |

## 8. 部署

- `push main` 触发 `.github/workflows/deploy.yml`；`docs/**` 与 `**.md` 改动被 `paths-ignore` 跳过，不会重建镜像。
- 镜像在 CI（buildx）构建并推阿里云 ACR，服务器只拉取运行。**服务器 1.6G 内存，禁止在服务器上构建镜像**。
- compose 服务：`app`（8000→127.0.0.1:8000）、`memory-worker`、`index-worker`、`db`（pgvector/pg16）、`caddy`。两个 worker 不暴露端口。
- 迁移在镜像启动流程里执行，部署后确认 `alembic current` 在 head。
- 生产服务器上的任何操作（重启、改配置、清库）**必须先征得用户同意**。

## 9. 提交与文档

- 按域拆提交（`refactor:` / `feat:` / `fix:` / `docs:`），保证单个提交可独立回滚、可独立运行。
- 不提交 `.env`、`data/`、`node_modules`、`dist`、`__pycache__`、数据库文件。
- 改了启动方式、目录结构、模块边界时，同步更新 `README.md` 与 `docs/architecture.md`；改了视觉规范时同步 `docs/design/`。