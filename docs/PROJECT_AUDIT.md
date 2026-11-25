# 归一 · Onefold 项目审计报告

- 审计日期：2026-11-24
- 审计方式：**只读静态审计**。未启动服务、未连接数据库、未修改任何代码。
- 判定依据：以**当前代码**为准；代码与既有文档冲突时，单独标注「文档过期」。
- 标注约定：
  - **【事实】** 可直接从代码/配置读出的结论，附文件路径。
  - **【建议】** 审计者判断，可被否决。
  - **【待确认】** 代码无法自证、需要产品或运行环境确认。

---

## 一、项目技术架构

### 1.1 后端

| 维度 | 实际内容 | 依据 |
|---|---|---|
| 语言/运行时 | Python 3.12 | `Dockerfile:35`（`python:3.12-slim`） |
| Web 框架 | FastAPI ≥0.115 + uvicorn[standard] | `backend/requirements.txt`、`app/main.py` |
| ORM | SQLAlchemy 2.0 **同步 Session**（非 async ORM） | `app/db.py` 的 `SessionLocal` / `get_db` |
| 数据库 | PostgreSQL 16 + pgvector | `docker-compose.yml`（`pgvector/pg16`）、`app/rag/query.py` |
| 迁移 | Alembic，4 个 revision | `backend/migrations/versions/` |
| 校验/配置 | pydantic v2 + pydantic-settings | `app/config.py` |
| 鉴权 | JWT（pyjwt）+ HttpOnly Cookie；密码 argon2 | `app/services/auth_session.py`、`app/api/deps.py` |
| 模型服务 | DeepSeek（OpenAI 兼容 SDK），`model=deepseek-flash` | `app/config.py`、`app/services/llm.py` |
| 向量化 | OpenRouter 的 `baai/bge-m3`，维度 1024 | `app/config.py`、`app/rag/embed.py` |
| 检索栈 | jieba 分词 → PG `tsvector` 词法 / BM25 / pgvector → RRF 融合 → 可选 rerank | `app/rag/*.py` |
| 文档解析 | pypdf、pdfplumber、python-docx、markdown | `app/rag/parse.py` |
| 异步生态 | httpx、tenacity、structlog、apscheduler | `requirements.txt` |
| MCP | `mcp>=2,<3`，**仅 stdio 且只有 hello 工具** | `app/mcp_server.py` |
| 规模 | `app/` 共 **7453 行**；**21 张表**；**41 个业务路由** + `/healthz` | `wc -l`、各 `__tablename__`、`@router.*` 统计 |
| 测试 | 9 个测试文件、**33 个用例** | `backend/tests/` |

数据表分组（**事实**，均无外键，靠应用层维护）：

- 账号：`users`、`email_codes`、`guest_sessions`、`visits`、`usage_daily`、`audit_logs`
- 对话：`conversations`、`runs`、`messages`、`tool_calls`、`conversation_summaries`
- 知识库：`knowledge_bases`、`documents`、`chunks`、`artifacts`、`skills`、`document_jobs`
- 记忆：`memory_settings`、`memory_items`、`memory_jobs`、`memory_events`

### 1.2 前端

| 维度 | 实际内容 | 依据 |
|---|---|---|
| 框架 | React 19 + TypeScript 5.7 + Vite 6 | `frontend/package.json` |
| 路由 | react-router-dom 7（`BrowserRouter`） | `src/main.tsx`、`src/App.tsx` |
| 状态 | zustand 5（单一 workspace store） | `src/store/workspace.ts` |
| 样式 | Tailwind 3.4，`darkMode: "class"` | `tailwind.config.js` |
| Markdown | react-markdown 9 + remark-gfm | `src/components/chat/MessageItem.tsx` |
| 图标 | Material Symbols Outlined（字体 ligature） | `src/components/ui/Icon.tsx`、`index.html` |
| 规模 | `src/` 共 **3834 行**（ts/tsx/css）；7 个页面、**33 个组件** | `find`/`wc -l` |

**已安装但全库未使用**（**事实**，逐项 grep 为 0）：

- `@tanstack/react-query`：`main.tsx` 挂了 `QueryClientProvider`，但无任何 `useQuery`/`useMutation`
- `rehype-sanitize`：Markdown 未做 HTML 消毒
- `lucide-react`：图标走 Material Symbols，未用 lucide

**资产加载风险【待确认】**：`index.html` 通过 `fonts.googleapis.com` 加载 Inter / Noto Sans SC / IBM Plex Mono / Material Symbols。图标是字体 ligature，**CDN 不可达时图标会退化成英文单词文本**（如 `close`、`search`），并撑破按钮尺寸。生产环境（境内服务器）能否稳定访问该 CDN，代码无法自证。

### 1.3 请求封装：目前四套并存（**事实**）

| 入口 | 覆盖范围 | 特征 |
|---|---|---|
| `lib/http.ts` → `apiRequest` | `lib/documents.ts`、`lib/memory.ts` | 统一带 Cookie，失败抛可读文案 |
| `lib/auth.ts` 私有 `request` | 登录/注册/验证码/重置 | 自带 JSON 头，错误走 `apiErrorText` |
| `lib/admin.ts` 私有 `call` | 后台用户/角色/用量 | 同上，另写一份 |
| 裸 `fetch` | `lib/chat.ts`、`lib/session.ts`、`lib/visit.ts`、`lib/sse.ts` | 分别处理 404、访客续期、`sendBeacon`、事件流 |

错误文案统一汇到 `apiErrorText` / `responseErrorText`（`lib/http.ts`），这是全站唯一文案出口。

**【建议】** 改版期间保持这层不动：`apiRequest` 已是稳定契约，UI 重做不应触碰请求层。

### 1.4 状态管理

- 全局单 store：`conversations / activeId / messages / ready / loading / error / running` + 外壳 UI（`navCollapsed`、`inspectorOpen`、`inspectorExpanded`、`focusMode`、`inspectorTab`）。
- `init()` 由模块级 `initialized` 守卫，**整个页面生命周期只执行一次**（`src/store/workspace.ts:39`）。
- 三个 Context：`AuthContext`（身份/配额）、`ThemeContext`（亮暗）、`ToastContext`（轻提示）。
- 页面局部状态：Chat 的输入框、Admin 的 tab/用户/用量、Documents 的 scope、各 hook 内部状态。

### 1.5 路由

`src/App.tsx` 中 `Routes` 共 7 条，全部静态 import（无代码分割）。

**缺口【事实】**：没有 `path="*"` 兜底路由，访问未知路径时只渲染外壳（侧栏），主区域空白。

### 1.6 主题系统与 Tailwind

- `tailwind.config.js`：`darkMode: "class"`，`theme.extend` 内含颜色/圆角/间距/字体/字号/过渡，无 preset。
- `index.html` 里有一段内联脚本，在首屏渲染前给 `<html>` 加 `.dark`，避免闪烁；`ThemeContext` 负责持久化 `onefold-theme`（默认 dark）。
- `index.css` 定义 `--of-*` CSS 变量（背景/前景/表面/描边/主色/滚动条），随 `.dark` 切换，供 `markdown.css` 与滚动条等**非 Tailwind 场景**取色。
- `theme.extend` 未覆盖 `borderColor`、`ringColor`、`boxShadow`、`screens`，这些仍用 Tailwind 默认值【待确认是否需要统一】。

---

## 二、页面清单

| 路由 | 入口文件 | 行数 | 主要功能 | 数据/状态来源 | 权限守卫 |
|---|---|---|---|---|---|
| `/` | `pages/Landing.tsx` | 43 | 品牌主张 + 4 张能力卡 + 三个入口链接 | 纯静态 | 无 |
| `/chat` | `pages/Chat.tsx` | 92 | 三栏研究工作区：顶栏 + 报告流 + 输入区 + 右侧检查器 | `store/workspace`、`useChatStream`、`AuthContext` | 无（访客可用，20 轮上限） |
| `/documents` | `pages/Documents.tsx` | 50 | 个人/公共知识库切换、上传、删除、收藏、重试、发布 | `useDocuments`（3s 轮询） | 公共库上传/删除需 `admin` |
| `/memory` | `pages/Memory.tsx` | 57 | 记忆开关、卡片/笔记列表、编辑、删除、清空 | `useMemory` | 无 |
| `/skills` | `pages/Skills.tsx` | 70 | Skill 列表 + 启用开关 | 直接 `apiRequest("/api/skills")` | 无（读操作） |
| `/admin` | `pages/Admin.tsx` | 91 | 用户管理（改角色/停用）+ 每日用量 | `lib/admin.ts` | 前端 `canUseAdmin`，后端 `require_admin` |
| `/login` | `pages/Login.tsx` | 59 | 登录 / 注册（邮箱验证码）/ 忘记密码三态 | `lib/auth.ts`、`AuthContext` | 无 |

补充【事实】：

- 页面容器不统一：`Landing/Documents/Admin` 用 `<PageFrame wide>`（max 1100），`Memory/Skills/Login` 用 `<PageFrame>`（max 860），`Chat` **不套 PageFrame**，自行 `flex h-full`。
- 全部页面由 `App.tsx` 在外层统一包了 `SideNav` + `main`，页面自身不渲染导航。
- 前端权限只在 Admin 页生效，其余页面不做入口隐藏；真正的越权判断都在后端。

---

## 三、组件清单

### 3.1 外壳与布局（`components/layout/`，7 个文件）

| 组件 | 行数 | 职责 | 使用方 |
|---|---|---|---|
| `SideNav.tsx` | 105 | 展开态左导航（240px）：品牌、新建、快速检索占位、模块导航、会话分组、身份区；并按 `navCollapsed` 切到 `NavRail` | `App.tsx` |
| `NavRail.tsx` | 85 | 收起态图标栏（60px） | `SideNav` |
| `ConversationGroups.tsx` | 71 | 近 20 天会话，按「今天/昨天/近 7 天/更早」分组 | `SideNav` |
| `NavUser.tsx` | 59 | 主题切换 + 头像 + 角色 + 退出/登录 | `SideNav` |
| `BrandMark.tsx` | 18 | 六边形双色 SVG 品牌标 | SideNav / NavRail / Landing / MessageList |
| `PageFrame.tsx` | 11 | 非聊天页容器：独立滚动 + 居中限宽（860/1100） | `App.tsx` 的 6 条路由 |
| `TopBar.tsx` | 69 | 旧版顶部导航 | **无引用（死代码）** |

### 3.2 聊天域（`components/chat/`，11 个文件）

| 组件 | 行数 | 职责 | 使用方 |
|---|---|---|---|
| `MessageList.tsx` | 69 | 报告流容器、空态示例问题、自动滚底、状态/错误行 | `Chat` |
| `MessageItem.tsx` | 42 | 单条消息：用户问题卡 / 助手 Markdown 报告 + 工具胶囊 + 抽屉 | `MessageList` |
| `ChatInput.tsx` | 78 | 输入区：Enter 发送、Shift+Enter 换行、三个 `Soon` 占位、发送/停止 | `Chat` |
| `WorkspaceHeader.tsx` | 50 | 顶栏：标题 + 专注模式 + 来源检查器开关 | `Chat` |
| `SourceInspector.tsx` | 94 | 右侧检查器：来源/记忆/工具/文档 4 个页签，320/440 两档 | `Chat` |
| `InspectorTools.tsx` | 47 | 检查器「工具」页：按工具罗列搜索结果/抓取页链接 | `SourceInspector` |
| `ToolDrawer.tsx` | 82 | 单条消息的工具明细抽屉（Esc 关闭、锁 body 滚动） | `MessageItem` |
| `ToolStatus.tsx` | 39 | 消息右上角胶囊：「正在搜索 / 搜索到 N 个网页」 | `MessageItem` |
| `RetrievalStatus.tsx` | 36 | 消息内可折叠的检索明细 | `MessageItem` |
| `QuotaBar.tsx` | 26 | 访客剩余轮次 / 用尽引导注册 | `Chat` |
| `ConversationList.tsx` | 59 | 旧版会话列表（`slate-*` 旧样式） | **无引用（死代码）** |

### 3.3 基础 UI 件（`components/ui/`，5 个文件）

| 组件 | 行数 | 导出 | 复用情况 |
|---|---|---|---|
| `kit.tsx` | 79 | `Card`、`PageHeader`、`PillTabs`、`Badge`、`EmptyText`、`ActionLink` | 被 **12** 个文件引用 |
| `table.tsx` | 23 | `TableShell`、`THead`、`Th`、`Td` | 被 **4** 个文件引用（DocTable / UserTable / UsageTable / Skills 页） |
| `form.tsx` | 40 | `fieldClass`、`TextInput`、`PrimaryButton`、`GhostButton` | 被 **4** 个 auth 组件引用 |
| `Icon.tsx` | 25 | Material Symbols 封装 | 几乎全部业务组件 |
| `Soon.tsx` | 35 | 「随后开放」禁用包装 + 悬停气泡 | 4 处（SideNav / NavRail / ChatInput / SourceInspector） |

其他：`components/common/ToastViewport.tsx`（32 行，唯一 `common/` 组件）、`documents/DocTable.tsx`（58）、`memory/MemoryCard.tsx`(27)、`admin/{UserTable,UsageTable,NoAccess}`、`auth/{LoginForm,RegisterForm,ResetForm,CodeField}`。

### 3.4 调用关系（**事实**，按代码里的 import）

```
App
├─ SideNav ─┬─ BrandMark
│           ├─ NavRail ─ BrandMark, Icon, Soon
│           ├─ ConversationGroups (store: conversations/activeId/running)
│           └─ NavUser (AuthContext, ThemeContext)
└─ Routes
   ├─ Landing ─ BrandMark, Icon, kit.Card
   ├─ Chat ─┬─ WorkspaceHeader (store: title/focus/inspector)
   │        ├─ MessageList ─┬─ MessageItem ─┬─ RetrievalStatus
   │        │               │               ├─ ToolStatus
   │        │               │               └─ ToolDrawer
   │        │               └─ BrandMark
   │        ├─ QuotaBar
   │        ├─ ChatInput ─ Icon, Soon
   │        └─ SourceInspector ─ InspectorTools, Soon
   ├─ Documents ─ DocTable, kit.*, useDocuments
   ├─ Memory ─ MemoryCard, kit.*, useMemory
   ├─ Skills ─ kit.*, table.*
   ├─ Admin ─ UserTable, UsageTable, NoAccess, kit.PillTabs
   └─ Login ─ LoginForm/RegisterForm/ResetForm ─ CodeField, form.*
```

### 3.5 死代码（**事实**，全库 import 数为 0）

| 文件 | 行数 | 说明 |
|---|---|---|
| `components/layout/TopBar.tsx` | 69 | 旧版顶栏，全部 `slate-*` 旧色 |
| `components/chat/ConversationList.tsx` | 59 | 旧版会话列表，全部 `slate-*` 旧色 |
| `hooks/useConversations.ts` | 85 | 旧版会话加载 hook，被 `store/workspace` 取代 |

【建议】改版前删除或明确标注，避免误改旧样式（本次审计不改）。

---

## 四、业务功能现状

### 4.1 已实现（**事实**）

| 功能 | 实现位置 | 说明 |
|---|---|---|
| 流式对话 | `api/chat.py` + `agent/runtime.py` + `lib/sse.ts` | SSE 事件：`queue` / `meta` / `token` / `tool_call` / `tool_result` / `done` / `error` |
| ReAct 工具循环 | `agent/runtime.py` | 最多 `agent_max_steps=10` 步，最后一步强制收尾 |
| 联网工具 | `agent/tools.py`、`services/tools/web.py` | `web_search`、`fetch_url`，带注入防护与审计落库 |
| 并发控制 | `services/concurrency.py` | 身份锁（同身份串行）+ 全局信号量 8 + 60s 排队超时 |
| 游客配额 | `api/chat.py`、`services/quota.py` | 20 轮，超限 403，前端识别后回滚消息 |
| 会话/历史 | `api/conversations.py`、`services/history*.py` | 近 20 天会话、按轮截断、超 token 压缩、run 回放 |
| 文档 RAG | `rag/*`、`api/documents.py`、`workers/document_index.py` | 词法+向量+BM25+RRF（rerank 可选）、父块扩展、引用元数据（文件名/页码/标题路径） |
| 公开知识库 | `api/knowledge.py` | 访客可读（`public_kb_guest_read=True`）、管理员发布/删除/重试 |
| 长期记忆 | `api/memory.py`、`services/memory_*.py`、`workers/memory*.py` | 提取队列、评分排序、按预算注入、会话级快照、前端可增删改 |
| 账号体系 | `api/auth.py`、`services/email_codes.py` | 邮箱验证码注册、登录、改密、访客转正 |
| 后台 | `api/admin.py` | 用户列表/角色/停用、每日用量、run 详情、存储统计 |
| 访问统计 | `api/visits.py`、`hooks/useVisitTracker.ts` | enter / heartbeat / leave，离开用 `sendBeacon` |

### 4.2 部分实现（**事实**，有代码但能力未闭环）

| 功能 | 现状 | 证据 |
|---|---|---|
| Skill | 只有「列表 + 启用开关」落库；**启用的 Skill 不会进入对话上下文** | `agent/context.py:47` 有 `skill_text` 参数，但 `runtime.py:81` 调用 `build_messages()` 时**未传**；无 `read_skill` 工具；`api/skills.py` 注释自称「骨架」 |
| 引用（citation） | 前端 `lib/sse.ts:161` 已处理 `citation` 事件；后端**从未发出该事件** | 后端 `sse_event(` 调用点只有 `queue/meta/error` + runtime 的 4 类 |
| 取消运行 | `POST /api/runs/{id}/cancel` 恒返回 `{"ok": true, "note": "TODO"}` | `api/chat.py:193-201` |
| MCP | stdio 只注册 `hello`；HTTP 入口返回 501 | `app/mcp_server.py`、`api/mcp.py` |
| 后台存储/run 详情 | 后端已实现，前端 `lib/admin.ts` 只调用 `users/role/status/usage` | `lib/admin.ts` |
| 游客画像报表 | 有 `visits` 表与上报，无任何查询接口/页面 | `api/admin.py` 无 visits 路由 |
| 检索 rerank | 代码完整，但 `rerank_enabled` 默认 `False` | `app/config.py` |
| 消息时间戳 | 后端返回 `created_at`，`lib/chat.ts` 的 `foldRows` 丢弃该字段；提问卡无时间 | `lib/chat.ts:63-96` |

### 4.3 仅 UI 占位（**事实**，全部用 `Soon` 包裹并提示「随后开放」）

| 占位 | 位置 |
|---|---|
| 快速检索（⌘K） | `SideNav.tsx`、`NavRail.tsx` |
| 检索范围 | `ChatInput.tsx` |
| 附加文档 | `ChatInput.tsx` |
| @ 引用知识库 | `ChatInput.tsx` |
| 来源对照面板 | `SourceInspector.tsx` 的 `SoonPanel` |

另有两个「跳转式」页签：检查器的「记忆」「文档」页签不展示数据，只给一句说明 + 跳转按钮（同文件 77-90 行）。

### 4.4 未实现 / 未接入

- 未知路由兜底页（`App.tsx` 无 `*`）
- 真实排队位置（`queue` 事件 `position` 恒为 0，代码注释已声明是骨架）
- 登录用户每日消息配额（`user_messages_per_day` 在 config 中标注「待接入」，全文无引用）
- MCP 只读工具与 HTTP 挂载
- 代码执行等更多内置工具（`agent/tools.py` 注释说明需自行扩展）

### 4.5 接口总览（**事实**）

41 个业务路由：`auth` 7、`admin` 6、`documents` 6、`knowledge` 6、`memory` 5、`chat` 2、`conversations` 2、`skills` 2、`mcp` 2、`visits` 3，另有 `/healthz`。

---

## 五、视觉系统现状

### 5.1 布局结构与主要尺寸

```
<html class="dark">
└ App: flex h-screen overflow-hidden
  ├ SideNav 240px（收起 60px） border-r
  └ main flex-1 min-w-0
    ├ Chat（不套 PageFrame）
    │  ├ section flex-1：WorkspaceHeader(sticky) → MessageList(max-w 800/820) → QuotaBar(800) → ChatInput(800)
    │  └ SourceInspector 320px / 展开 440px（<1280 为 fixed 浮层 + 遮罩）
    └ 其他页：PageFrame（max-w 860 / wide 1100，px-32 py-24，独立滚动）
```

| 区域 | 尺寸常量 | 出处 |
|---|---|---|
| 左导航展开/收起 | 240px / 60px | `SideNav.tsx:28`、`NavRail.tsx:26` |
| 顶部栏 | `px-gutter-xl(32) py-gutter-md(16)`，sticky z-10 | `WorkspaceHeader.tsx:28` |
| 报告画布 | 常宽 800 / 专注 820，`px-32 py-32`，条目间距 32 | `MessageList.tsx:34` |
| 输入卡 | 800，`px-16 py-8` | `ChatInput.tsx:20` |
| 检查器 | 320 / 440，`max-w-[92vw]` | `SourceInspector.tsx:43` |
| 登录卡 | `max-w-sm`（384） | `Login.tsx:35` |
| 表格 | 通栏 + 横向滚动 | `table.tsx` |

**任意值（`[NNNpx]`）共 13 种**，集中在上述宽度：`800×4`、`860`、`820`、`60`、`520`、`440`、`420`、`40`、`320`、`240`、`220`、`1100`、`10`。

### 5.2 Token（**事实**，全部来自 `tailwind.config.js`）

- 颜色：`light-*` / `dark-*` 成对，Material-3 鼠尾草绿。主色 `light-primary #648B54` / `dark-primary #B6E3A1`；背景 `#F7F8F6` / `#101315`；表面 `#FFFFFF` / `#171C1F`；描边 `#E5E9E3` / `#2A3235`；错误 `#B91C1C` / `#F87171`。
- 圆角：`sm 6` / `DEFAULT 8` / `md 12` / `lg 16` / `full`。
- 间距：`gutter-xs 4` / `sm 8` / `md 16` / `lg 24` / `xl 32` / `section 48` / `page-margin 24`。
- 字号：`headline-lg 24/32`、`headline-md 18/26`、`title-md 15/22`、`body-md 15/27`、`body-sm 14/22`、`label-lg 14`、`label-md 13`、`label-sm 12`、`mono-sm 12`。
- 字体：`headline/title Inter`、`body/label Noto Sans SC`、`mono IBM Plex Mono`。
- 过渡：`duration-state-change 120ms` + `ease-out`。
- **未被使用的 token**：`spacing.page-margin`（全库 0 引用）、`borderRadius.lg`（0 引用）。

### 5.3 Light / Dark

- 默认 **dark**（`ThemeContext` 与 `index.html` 都如此），可切 light，持久化在 `localStorage["onefold-theme"]`。
- 成对类计数：`light-*` **280** 次、`dark-*` **280** 次，**一一配对，没有单向样式**（**事实**，grep 统计）。这是当前代码质量最好的一点。
- 非 Tailwind 场景（Markdown、滚动条、流式光标）走 `--of-*` 变量，两套主题各自定义。

### 5.4 全局样式与局部样式

- 全局：`index.css`（121 行）= Tailwind 三件套 + `--of-*` 变量 + Material Symbols 尺寸锁 + 滚动条 + `toast-in` 动画 + 流式光标 `.of-caret`。
- 全局：`markdown.css`（97 行）= `.markdown` 下的标题/段落/列表/代码块/表格/引用/链接，全部取 `var(--of-*)`，无硬编码颜色。
- 局部：**所有组件样式都写在 className 里**，无 CSS Module、无 `@layer components`、无 `@apply`。
- **TSX 中硬编码 hex：0 处**（**事实**）；`slate-*` 只出现在两个死代码文件里。

### 5.5 与既有设计规范的偏差（**事实**，对照 `docs/design/STYLE_SPEC.md`、`LAYOUT_SPEC.md`）

| 规范要求 | 当前实现 |
|---|---|
| `focus-visible: outline-2 primary`（新建/发送） | 全库 **0 处** `focus-visible`；只有输入框有 `focus:border-primary` |
| 卡片/表格容器圆角 8px | `Card`、`TableShell` 用 `rounded-md`（**12px**） |
| 小按钮/徽章圆角 6px | `form.tsx` 的按钮用 `rounded`（8px） |
| 四份设计稿均无 box-shadow | 现有 `shadow-2xl ×2`（检查器/抽屉）、`shadow-lg ×2`（Soon 气泡/Toast） |
| 左导航有 224px 紧凑态 | 只有 240px 与 60px 两态 |
| 顶栏主态含元信息行（范围/时间/参考数） | 无元信息行，只有标题 + 两个按钮 |
| 提问卡含时间（mono-sm） | 无时间 |

---

## 六、代码问题

### 6.1 影响 UI 改版的结构问题

1. **没有布局原语**：页面宽度靠 `PageFrame` 的 `wide` 布尔和散落各处的 `max-w-[NNNpx]`，共 13 种任意宽度值。改一版间距要改十几处。
2. **导航与数据耦合**：`SideNav`（105 行）同时管品牌、新建、导航项、会话列表、身份区；会话列表直接读 store。改版时无法单独替换侧栏视觉。
3. **Chat 与其它页两种外壳**：Chat 用 `flex h-full` 自管滚动，其它页用 `PageFrame` 包裹。任何"统一页面内边距"的诉求都要分两套处理。
4. **页面即容器**：`Chat.tsx` 直接写遮罩 + 条件渲染检查器（92 行的编排里混了响应式布局逻辑）。
5. **抽屉/浮层无统一层**：`ToolDrawer` 自建 `fixed inset-0 z-50`，检查器自己写 `fixed inset-y-0 right-0 z-40` + 遮罩在页面层，`Toast` 是 `z-50`。z-index 无统一分层表。
6. **样式全在 className**：280 对主题类散落在 33 个组件中，没有语义层（如 `surface-card`、`text-muted`），改视觉必须全库替换。
7. **死代码占位**：`TopBar`、`ConversationList` 保留旧 `slate-*` 样式，搜索类名会命中它们，容易改错。
8. **图标依赖字体 CDN**：见 1.2，视觉与网络强绑定。

### 6.2 重复样式

| 重复项 | 出现位置 |
|---|---|
| 主色实心按钮 | `Landing` 的「开始研究」、`PillTabs` 选中态、`form.PrimaryButton`、`SideNav` 新建、`ChatInput` 发送 —— 5 处各写一遍 |
| 描边幽灵按钮 | `Landing`、`Documents` 上传 label、`form.GhostButton`、`WorkspaceHeader.btn`、`SourceInspector` 两个跳转按钮 |
| 面板卡壳（圆角+描边+surface） | `kit.Card`、`table.TableShell`、`RetrievalStatus`、`MessageItem` 用户卡、`ChatInput` 外框、`InspectorTools` 链接卡 |
| 错误文字色 | `LoginForm`、`RegisterForm`、`ResetForm`、`CodeField`、`MessageList`、`DocTable` 各写一遍 `text-light-error dark:dark-error` |
| 「执行动作 → toast → 重新加载」 | `useDocuments.run`、`useMemory.run`、`Admin.run` 三份近似实现 |

### 6.3 组件职责不清

| 组件 | 问题 |
|---|---|
| `SideNav.tsx` | 一个文件里 5 类职责（品牌/主操作/导航/会话/身份），且条件决定渲染 `NavRail` |
| `SourceInspector.tsx` | 4 个页签内容全部内联，其中 2 个是占位、2 个是跳转，真正的业务面板只有 `InspectorTools` |
| `MessageItem.tsx` | 兼管用户卡、助手报告、工具胶囊、抽屉开关 4 件事；已经接近 120 行上限 |
| `Chat.tsx` | 编排 + 遮罩 + 响应式断点逻辑混在一起 |

### 6.4 改动时的依赖风险（**事实**）

1. `store/workspace.ts` 的 `initialized` 是**模块级变量**：热更新或重复挂载不会重新初始化；改外壳状态时不要顺手改 `init` 的守卫。
2. `useChatStream` 通过 `setMessages` / `onConversation` / `onRoundDone` 与 store、Auth 双向回调：改消息模型会连带影响配额刷新与侧栏排序。
3. `lib/chat.ts` 的 `foldRows` 决定「一轮 = 一个气泡 + tools 数组」，`MessageItem`/`ToolStatus`/`ToolDrawer`/`InspectorTools` 都依赖这个结构。
4. 配额判定依赖文案：`isQuotaError` 判断 `status===403 && message.includes("注册")`（`lib/sse.ts:80`）。**改后端 403 文案会直接让配额提示失效**。
5. `Soon` 被 4 处依赖；直接删组件会让「尚未开放」的功能变成可点击的假按钮。
6. 前端 `foldRows` 用 `tool_ok` 兜底成败，依赖 `tool_calls.data_json` 与审计表字段；改数据结构会影响历史回放。

### 6.5 无障碍与交互（**事实**）

- `focus-visible` 全局 0 处：键盘 Tab 看不到焦点（仅有输入框的 `focus:` 描边）。
- 两个浮层（`ToolDrawer`、窄屏检查器）没有 `role="dialog"` / `aria-modal`，也没有焦点陷阱；`ToolDrawer` 只处理了 Escape 与 body 滚动锁定。
- Toast 已具备 `aria-live="polite"` + error `role="alert"`，是全站无障碍做得最好的一处。
- 记忆编辑用 `window.prompt`、删除用 `window.confirm`（`useMemory.ts:58,64,69`），视觉与浏览器原生强绑定。

### 6.6 文档过期（**事实**）

| 位置 | 过期内容 | 现状 |
|---|---|---|
| `backend/app/agent/runtime.py:59` | 「retrieve 目前是空骨架，返回 []」 | `rag/retrieve.py` 已完整实现 |
| `docs/architecture.md`「待实现」1、2 条 | retrieve 骨架、文档上传未暴露 | 两者均已实现 |
| `docs/architecture.md`「待实现」3 条 | 后台 run 回放/访客报表/每日配额 | run 回放与存储统计已实现；访客报表、每日配额仍未做 |

---

## 七、UI 改版建议

> 以下全部是【建议】，与第六节的【事实】分开。

### 7.1 建议原样保留（不动结构，只换皮肤）

| 对象 | 理由 |
|---|---|
| `lib/http.ts`、`lib/sse.ts`、`lib/chat.ts`、`lib/memory.ts`、`lib/documents.ts`、`lib/auth.ts`、`lib/admin.ts`、`lib/session.ts` | 请求与协议层，与视觉无关；动它风险最高 |
| `store/workspace.ts` | 外壳状态（nav/inspector/focus）已按视觉需求抽象好 |
| `hooks/useChatStream.ts` | 流式状态机，含配额回滚等关键逻辑 |
| `context/{Auth,Theme,Toast}` | 三套全局态职责清晰 |
| `ui/Icon.tsx`、`ui/form.tsx`、`ui/table.tsx`、`ui/Soon.tsx` | 可复用基础件，改版应在此基础上扩展而非重写 |
| `DocTable`、`UserTable`、`UsageTable`、`NoAccess` | 纯展示 + 回调，列结构稳定 |
| `ToastViewport` | 可访问性已达标 |

### 7.2 建议调整（保留逻辑，调结构/样式）

| 对象 | 调整方向 |
|---|---|
| `SideNav` / `NavRail` | 按「品牌区 / 主操作区 / 导航区 / 会话区 / 身份区」拆成 5 个子组件，侧栏宽度与紧凑态做成 prop；顺带补 224px 紧凑态或明确取消该状态 |
| `PageFrame` | 增加 `width: "narrow" \| "regular" \| "wide"` 与 `scroll` 开关，收敛所有 `max-w-[NNNpx]` |
| `MessageList` / `MessageItem` | 抽出 `ReportBody`（Markdown 排版）与 `UserQuestionCard`、`ToolSummary`，让单文件回到 120 行内 |
| `SourceInspector` | 拆成 `InspectorTabs` + `InspectorSources/Memory/Docs/Tools` 四个面板；记忆/文档面板可接真实数据（数据已在 `lib/*` 中） |
| `ChatInput` | 把 `Soon` 工具条抽成 `ComposerToolbar`，方便以后替换为真实功能 |
| `WorkspaceHeader` | 增加规范里的元信息行（范围/时间/参考数），数据可从 store + 消息数量推导 |
| `kit.tsx` | 补 `SurfaceCard`、`TextButton` 等语义件，减少 6.2 的重复 |
| `Tailwind` | 建议把圆角/阴影/聚焦环补成规范值，并把 `focus-visible` 做成全局默认（`@layer base`）而不是逐组件写 |

### 7.3 建议重做

| 对象 | 原因 |
|---|---|
| `markdown.css` | 目前是"能读"级别（97 行、纯 CSS 变量）。设计稿要求 h2 章节化、核心结论竖线、表格主数值强调，需要按新排版规范重写 |
| 视觉 token 层（`tailwind.config.js` 的 colors/radius/spacing） | 若确定换风格（如文献风），token 要一次性换掉；但**必须保持 `light-*`/`dark-*` 成对命名**，否则 280 对类名要全改 |
| 浮层体系 | 建议引入统一的 `Overlay`（含遮罩、z-index 分层、Escape、焦点陷阱），替换 `ToolDrawer` 与窄屏检查器的各自实现 |
| `components/layout/TopBar.tsx`、`components/chat/ConversationList.tsx`、`hooks/useConversations.ts` | 死代码，重做前先移除（不新增、只删除旧实现，需你确认） |

### 7.4 改造时必须保护的业务功能（回归清单）

1. **SSE 事件契约**：`queue/meta/token/tool_call/tool_result/done/error` 的名称与 payload 字段。
2. **工具调用展示**：`ToolRun` 的 running/ok/error 三态与 `data.items / data.kind` 结构。
3. **配额逻辑**：`isQuotaError` 的 403 + "注册" 文案匹配；前端回滚已插入的问答对。
4. **运行中禁用**：`running` 时禁新建/切会话/禁输入（`SideNav`、`ConversationGroups`、`ChatInput` 三处）。
5. **身份与权限**：`me.kind === "guest"` 的引导分支、`canUseAdmin/canManageUsers` 的前后端一致性。
6. **历史折叠**：`foldRows` 的输出结构（一轮一气泡 + tools 数组）。
7. **暗亮配对**：任何新样式必须同时给 `dark:` 变体（当前 280/280 是硬性基线）。
8. **占位语义**：`Soon` 包裹的 5 个入口必须仍然不可点击。
9. **首屏主题脚本**：`index.html` 的内联脚本与 `ThemeContext` 的 key（`onefold-theme`）不能改名。
10. **检查器开关三态**：`inspectorOpen × inspectorExpanded × focusMode` 的组合关系（`WorkspaceHeader.toggleInspector` 有专门分支）。

### 7.5 建议的改造顺序（不改业务逻辑）

1. 删除 3 个死代码文件 → 2. 收敛布局原语（`PageFrame` 宽度档位 + `Overlay`）→ 3. 拆 `SideNav` / `SourceInspector` / `MessageItem` → 4. 换 token 与 `markdown.css` → 5. 逐页替换 className → 6. 补 `focus-visible` 与键盘回归。

---

## 八、核心文件索引（改版优先阅读）

### 后端

| 文件 | 职责 | 改版关注度 |
|---|---|---|
| `backend/app/api/chat.py` | SSE 对话入口、并发闸门、配额拦截 | 高（事件契约） |
| `backend/app/agent/runtime.py` | ReAct 循环，产出 token/tool 事件 | 高 |
| `backend/app/agent/context.py` | system/历史/RAG 组装（含 `skill_text` 未接线） | 高 |
| `backend/app/agent/tools.py` | 工具注册表（仅 web_search / fetch_url） | 中 |
| `backend/app/rag/retrieve.py` | 混合检索主流程与降级 | 中 |
| `backend/app/rag/query.py` | 词法/向量候选与父块加载 | 中 |
| `backend/app/api/documents.py`、`api/knowledge.py` | 文档上传/重试/收藏/发布 | 中 |
| `backend/app/api/memory.py`、`services/memory_context.py` | 记忆读写与注入格式 | 中 |
| `backend/app/api/auth.py`、`services/auth_session.py` | 身份与 Cookie | 低 |
| `backend/app/config.py` | 所有预算/开关（rerank、RAG、配额、上下文） | 高 |

### 前端

| 文件 | 职责 | 改版关注度 |
|---|---|---|
| `frontend/tailwind.config.js` | 全部视觉 token | 最高 |
| `frontend/src/index.css` | 全局变量、滚动条、图标尺寸锁、动画 | 最高 |
| `frontend/src/markdown.css` | 报告排版 | 高 |
| `frontend/src/App.tsx` | 路由 + 外壳骨架 | 高 |
| `frontend/src/components/layout/SideNav.tsx` | 240px 侧栏全部内容 | 高 |
| `frontend/src/components/layout/NavRail.tsx` | 60px 收起态 | 高 |
| `frontend/src/components/layout/PageFrame.tsx` | 非聊天页容器 | 高 |
| `frontend/src/components/chat/MessageList.tsx` | 报告画布宽度与空态 | 高 |
| `frontend/src/components/chat/MessageItem.tsx` | 单条消息排版 | 高 |
| `frontend/src/components/chat/ChatInput.tsx` | 输入区与占位工具条 | 高 |
| `frontend/src/components/chat/WorkspaceHeader.tsx` | 顶栏与两个开关 | 高 |
| `frontend/src/components/chat/SourceInspector.tsx` | 右侧检查器 | 高 |
| `frontend/src/components/ui/kit.tsx` | 卡片/页头/页签/徽章/空态/文字按钮 | 最高 |
| `frontend/src/components/ui/{form,table,Icon,Soon}.tsx` | 表单/表格/图标/占位 | 高 |
| `frontend/src/store/workspace.ts` | 外壳与消息状态（含 5 个 UI 开关） | 最高 |
| `frontend/src/lib/{http,sse,chat}.ts` | 请求、事件流、历史折叠 | 只读，禁改 |
| `frontend/src/context/ToastContext.tsx` + `components/common/ToastViewport.tsx` | 轻提示 | 中 |
| `frontend/src/pages/*.tsx` | 7 个页面编排 | 中 |

---

## 九、审计局限（需人工确认）

1. **运行期表现未验证**：本次未启动服务，未在浏览器实机核对窄屏断点、滚动、暗亮切换；`<1280` 检查器浮层与 `xl` 断点的实际效果属静态推断。
2. **构建产物未重跑**：历史记录为 `506.99 kB / gzip 158.13 kB`，本次未执行 `npm run build`。
3. **设计稿原件未读取**：`docs/design/*` 是既有逆向文档，本次以它为准比对代码；与最新 Figma 是否一致**待确认**。
4. **MCP 运行时行为**：`mcp>=2` 的 `MCPServer` 用法是否与所装版本完全匹配，需实跑确认。
5. **Skill 是否另有外部注入路径**：本次全库 grep `skill` 只命中 `api/skills.py` 与 `context.py` 的参数，判定"未接线"；若未来通过其他方式注入，需更新本条。
6. **Google Fonts 可达性**：境内生产环境能否加载 Material Symbols，直接决定图标是否可用，需线上验证。