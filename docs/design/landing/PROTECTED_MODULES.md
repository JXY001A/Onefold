# 保护模块清单

## P0 —— 原则上零修改（任何改动需单独批准）

- `backend/**` 全部（含未提交的 `workers/runner.py`）。
- `frontend/src/lib/**`（http / sse / chat / documents / memory / auth）。
- `frontend/src/hooks/**`（useChatStream / useConversations / useDocuments / useMemory / useVisitTracker）。
- `frontend/src/store/**`（workspace）。
- `frontend/src/context/**`（Auth / Theme / Toast）。
- 应用页面与组件：`pages/{Chat,Documents,Memory,Skills,Admin,Login}.tsx` 及 `components/{chat,documents,memory,skills,admin,auth,ui,common,pages}/**`。
- `docs/design/` 下的 13 份既有文档。
- `.env.example`、`docker-compose.yml` 及任何未提交文件。

## P1 —— 允许受限修改（必须说明风险并回归）

| 文件 | 允许的修改 | 风险与回归 |
|---|---|---|
| `frontend/src/App.tsx` | 仅路由外壳拆分：`/` 移出 SideNav shell（嵌套路由 + Outlet），其余路由不动 | 波及全部路由的挂载方式；须回归 6 条路由 + 主题切换 + 访问统计 |
| `frontend/tailwind.config.js` | 仅新增 `cosmic` 色组（纯增量） | 理论上零影响；构建后抽查其他页面样式无变化 |
| `frontend/index.html` | 计划不修改（字体已齐备） | — |

## P2 —— 本次施工范围（允许按设计重建）

- `frontend/src/pages/Landing.tsx`（重写）
- `frontend/src/components/landing/**`（全部新建）
- `frontend/public/landing/**`（截图素材）

## 铁律

1. 不修改 P0 内任何文件；发现必须修改时暂停并请示。
2. 不扩大修改范围；不以「顺手优化」为由触碰范围外代码。
3. 不覆盖未提交改动；施工前检查 `git status`。
4. 每阶段结束后 `git diff` 只应包含本阶段清单内文件。
