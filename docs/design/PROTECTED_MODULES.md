# 保护模块清单（五页改造）

> 分析模式产物，未修改源代码。等级：P0 零修改（需用户批准才可动）、P1 允许必要局部修改并说明风险、P2 可按设计调整但不得破坏契约、P3 本次允许重构的纯视觉组件。

## P0：业务核心，原则零修改

| 模块 | 保护内容 |
|---|---|
| `lib/http.ts` | `apiRequest`（credentials）、`apiErrorText` 双形状错误解析、状态码兜底 |
| `lib/sse.ts` | SSE 解析、`streamChat` 事件协议、`isQuotaError`（403+「注册」） |
| `lib/chat.ts` | `foldRows`、`fetchConversations`、`fetchMessages`、`formatTime`、`ToolRun`/`ChatMessage` 类型 |
| `store/workspace.ts` | `initialized` 守卫、全部 UI 开关、会话动作；不新增字段（C6） |
| `hooks/useChatStream.ts` | patchLast、quota 回滚、AbortError 静默、finally 回调 |
| 后端 | 任何 API、数据库结构、Prompt、工具定义均不得为本次 UI 改造而改 |

## P1：接口契约与共享壳，允许局部修改

| 模块 | 约束 |
|---|---|
| `context/AuthContext.tsx` | `me`/`loading`/`setMe` 语义不变；登录成功回写身份 |
| `context/ThemeContext.tsx` | 主题切换与预涂脚本不变 |
| `context/ToastContext.tsx` | `push(level, text)` 契约不变 |
| `lib/auth.ts` / `lib/session.ts` | 登录、注册、验证码、重置、访客会话流程不变 |
| `lib/admin.ts` | 用户/用量字段与 PATCH 契约不变 |
| `lib/documents.ts` | 上传、删除、重试、发布、收藏的 URL 与方法不变 |
| `lib/memory.ts` | 记忆读取与增删改契约不变 |
| `hooks/useMemory.ts` / `hooks/useDocuments.ts` | 加载、错误提示、轮询节奏（3s）不变；可在不改契约前提下增加只读派生 |
| `App.tsx` | 路由表与外壳；仅允许为页面视觉做不改变路由/滚动模型的最小调整 |
| `SideNav.tsx` / `NavRail.tsx` | 共享导航壳：保持路由、权限过滤、会话切换、新建、主题、身份区行为；不得因五页视觉而破坏工作区 |

## P2：共享视觉组件，可调整但需全站回归

| 模块 | 影响范围 |
|---|---|
| `ui/kit.tsx`（Card/PageHeader/PillTabs/Badge/EmptyText/ActionLink） | 五页 + 后台/账号等；改动需逐页回归 |
| `ui/form.tsx`（TextInput/PrimaryButton/GhostButton） | 登录/注册/重置 |
| `ui/table.tsx`（TableShell/THead/Th/Td） | 后台/知识库/Skill；改动影响三页 |
| `ui/Icon.tsx` | 全站图标；只允许尺寸/名称调用，不改渲染机制 |
| `ui/Soon.tsx` | 工作区与检查器占位；不得改变禁点与提示行为 |

## P3：本次允许改造的纯视觉组件

- `pages/Login.tsx`、`components/auth/*`
- `pages/Admin.tsx`、`components/admin/*`
- `pages/Documents.tsx`、`components/documents/*`
- `pages/Skills.tsx`
- `pages/Memory.tsx`、`components/memory/*`

## 红线

1. 不修改后端接口、数据库、依赖与构建配置。
2. 不为视觉新增业务字段（如收藏态、发布时间）——先记录缺口并等待决策。
3. 不伪造数据、不伪造权限、不伪造状态。
4. 共享组件改动必须回归五个页面之外的使用方（工作区、Landing、检查器等）。
5. 发现设计与业务冲突时暂停，先记录再确认。
