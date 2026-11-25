# 五页改造基线审计（登录 / 后台 / 知识库 / Skill / 记忆）

> 分析模式产物，未修改任何源代码。基线时点：2026-11-25；工作树干净，HEAD `47fd34a`（已包含上一轮工作区 UI 改版）。
> 基线验证：`npx tsc -b` 通过；`npm run build` 通过（Vite 6.4.6，约 1.2s）。

## 1. 基线状态

| 项目 | 结果 |
|---|---|
| Git | `git status` 干净；`git diff` 为空；HEAD 含全部 18 个工作区改造文件 |
| TypeScript | 通过，0 错误 |
| 构建 | 通过，仅有既有 chunk >500kB 提示 |
| 五个页面文件 | Login/Admin/Documents/Skills/Memory 自 11-24 起未变 |
| 运行依赖 | 后端与前端均可用；本轮分析未启动服务 |

## 2. 五页现状审计

### 登录 `/login`
- 文件：`pages/Login.tsx` + `components/auth/{LoginForm,RegisterForm,ResetForm,CodeField}.tsx` + `components/ui/form.tsx`。
- 结构：标题+说明、已登录提示、PillTabs 三态、Card 表单；成功后跳回来源页。
- 数据/接口：`/api/auth/login`、`/register`、`/email-code`、`/reset-password`；验证码 6 位、60s 冷却、dev 码提示。
- 状态：忙碌/错误/禁用（账号空、密码 <8、验证码 ≠6）。
- 与设计差异：仅措辞占位（设计示例「例如：周岚」）与已登录提示样例；功能一致。

### 后台 `/admin`
- 文件：`pages/Admin.tsx` + `components/admin/{UserTable,UsageTable,NoAccess}.tsx`。
- 权限：`canUseAdmin`（管理员/超管）；写操作仅超管；超管行不可改。
- 数据：`/api/admin/users`、`/api/admin/usage`；用户字段 id/username/email/role/status/created_at；用量 user_id/day/messages/tokens_in/tokens_out/tool_calls。
- 状态：加载「加载中…」、无权限页、空表、忙碌禁用、toast 错误。
- 与设计差异：设计新增页头说明「查看团队成员角色状态与每日模型调用用量。」；其余一致。

### 知识库 `/documents`
- 文件：`pages/Documents.tsx` + `components/documents/DocTable.tsx` + `hooks/useDocuments.ts` + `lib/documents.ts`。
- 能力：个人/公共页签；上传（单文件 input）、轮询 3s、删除、重试（failed）、发布到公共（个人+超管+ready）、收藏（仅 personal+temp）。
- 字段：id/kb_id/scope/public|personal|temp/filename/size/kind/status/error/page_count/chunk_count/expires_at。
- 与设计差异（B 类，需确认）：
  1. 设计有拖拽上传区与「上传 → 解析」流水线；当前仅文件选择器（家族 A 页面未含拖拽，家族 B 才有）。
  2. 设计显示「管理员发布于 …」「已收藏」与公共文档「收藏」；Doc 类型无发布人/发布时间/收藏态，且后端收藏接口要求文档拥有者，公共文档收藏会 403/404。
  3. 设计标注「公共文档不可删除」；当前非管理员本就无删除入口，现有权限已满足；超管删除不改变。
  4. 设计状态与分块信息同行、表格圆角 8、窄屏卡片列表；当前为两行、圆角 12、横向滚动。

### Skill `/skills`
- 文件：`pages/Skills.tsx` + `ui/table.tsx`。
- 能力：`GET /api/skills`，`POST /api/skills/{id}/enable`；列 名称/版本/状态/操作；空态与启停 toast。
- 与设计差异：无功能差异，仅视觉核对。

### 记忆 `/memory`
- 文件：`pages/Memory.tsx` + `components/memory/MemoryCard.tsx` + `hooks/useMemory.ts` + `lib/memory.ts`。
- 能力：`/api/memory` 读取、开关、编辑（prompt）、删除、清空；卡片/笔记两区块；关闭横幅；加载/失败/空态。
- 与设计差异：无功能差异；设计额外提供浅/深与关闭态画面，作为视觉验收用例。

## 3. 权限与状态矩阵

| 能力 | 游客 | 成员 | 管理员 | 超管 |
|---|---|---|---|---|
| 登录/注册/找回 | ✅ | ✅ | ✅ | ✅ |
| 后台查看 | ❌ | ❌ | ✅（只读） | ✅ |
| 改角色/停用 | ❌ | ❌ | ❌ | ✅ |
| 个人文档上传/删除 | ✅ | ✅ | ✅ | ✅ |
| 公共文档上传/删除 | ❌ | ❌ | ✅ | ✅ |
| 发布到公共 | ❌ | ❌ | ✅ | ✅ |
| Skill 启停 | ✅ | ✅ | ✅ | ✅ |
| 记忆查看/启停/编辑/清空 | ✅ | ✅ | ✅ | ✅ |

## 4. 保护模块（详见 PROTECTED_MODULES.md）

- P0：`lib/http.ts`、`lib/sse.ts`、`lib/chat.ts`、`store/workspace.ts`、`hooks/useChatStream.ts`。
- P1：`context/{Auth,Theme,Toast}Context.tsx`、`lib/{auth,admin,documents,memory,session,roles}.ts`、`hooks/{useMemory,useDocuments}.ts`、App 路由壳、共享导航壳。
- P2：`ui/kit.tsx`、`ui/form.tsx`、`ui/table.tsx`、`ui/Icon.tsx`、`ui/Soon.tsx`。
- P3：五个页面的页面组件与页面专属子组件。

## 5. 基线结论

1. 用户已定版：知识库/Skill/记忆以 Onefold 2.0 为视觉依据；登录/后台暂无 2.0 稿，按家族 A 执行；公共文档收藏不做。
2. 2.0 三页为三栏结构（240/820/320）并依赖多项后端能力；当前五页为单栏 PageFrame，功能与设计语义仅部分对应。
3. 当前构建健康（tsc/build 通过，工作树干净），可在此基线上分阶段改造。
4. 在 2.0 深色稿、登录/后台 2.0 稿补齐前，只能完成部分页面与浅色验收；施工前需确认「视觉壳 + 真实数据 + 缺失能力省略」的边界。
