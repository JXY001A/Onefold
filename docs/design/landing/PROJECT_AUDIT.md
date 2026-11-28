# 项目现状审计（落地页改版前置）

> 分析模式产物。审计对象：`/Users/jinxianyu/code/onefold`。

## 1. 技术栈

React 19 / Vite 6 / TypeScript 5.7 / react-router-dom 7 / zustand 5 / @tanstack/react-query 5 / Tailwind 3.4 / react-markdown 9 / clsx + tailwind-merge。字体 Inter + Noto Sans SC + IBM Plex Mono 与 Material Symbols 均已在 `frontend/index.html` 加载。

## 2. 设计 Token 现状（`frontend/tailwind.config.js`）

- 颜色：Material-3 鼠尾草绿体系，`light-*` / `dark-*` 成对 27 组（primary/secondary/warning/success/error/background/surface 5 级/on-*/outline）。
- 圆角 6/8/12/16/9999；间距 gutter-xs~xl + section + page-margin；字号 9 档 24→12px；断点沿用默认（sm 640 / lg 1024）。
- 全局 CSS 变量：`src/index.css` 的 15 个 `--of-*`，供 markdown.css 与全局样式使用。
- **与本次设计的关系**：新落地页是独立的宇宙蓝紫语言，不复用、也不得改动上述 token。

## 3. 路由与外壳

`src/App.tsx:27-43`：全局 shell = SideNav + main 两栏，所有路由（含 `/`）都在 shell 内渲染。

| 路由 | 页面 | 行数 |
|---|---|---|
| `/` | Landing.tsx（旧版落地页，PageFrame wide 容器内） | 43 |
| `/chat` | Chat.tsx | 92 |
| `/documents` | Documents.tsx | 79 |
| `/memory` | Memory.tsx | 95 |
| `/skills` | Skills.tsx | 77 |
| `/admin` | Admin.tsx | 104 |
| `/login` | Login.tsx | 86 |

旧 Landing 内容（「万般能力，归一入口」+ 4 张能力卡）将被设计稿内容整体替换（路线 P2，纯视觉页，无业务逻辑）。

## 4. 业务相关（本次不触碰）

- SSE 流式对话、来源检查器、记忆/文档/Skill 管理均与本页无关；落地页无任何 API 调用，天然无虚假数据风险。
- 访问统计 `useVisitTracker` 挂在 App 级，落地页独立后仍生效（保持现状）。

## 5. 工程约束

- 单文件 ≤200 行、React 组件 ≤120 行 → 落地页必须拆分。
- 目录惯例：域组件放 `src/components/<domain>/`；页面在 `src/pages/` 只做编排。
- 图标统一走 Material Symbols（设计稿同款），无需引入 lucide。

## 6. 仓库状态（施工前快照）

未提交改动：`.env.example`、`backend/app/workers/runner.py`、`docker-compose.yml`、`frontend/src/components/chat/ChatInput.tsx`——**均不在本次施工范围内，不得覆盖**。
`docs/design/` 已有 13 份既有设计文档（Onefold 2.0 家族），本批文档写入新目录 `docs/design/landing/`，不修改旧文档。
`frontend/public/` 目前为空，素材目录需新建。
