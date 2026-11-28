# 保护模块清单（记忆中心改版）

## P0 —— 原则上零修改（任何改动需单独批准）

- `backend/**` 全部（本次不改后端；现有记忆 API 作为契约基线）。
- `frontend/src/lib/http.ts`、`sse.ts`、`chat.ts`、`documents.ts`。
- `frontend/src/hooks/{useChatStream,useConversations,useDocuments,useVisitTracker}.ts`。
- `frontend/src/store/**`、`frontend/src/context/**`（Auth/Theme/Toast）。
- 其他页面与组件：`pages/{Chat,Documents,Skills,Admin,Login,Landing}.tsx`、`components/{chat,documents,skills,admin,auth,ui,pages}/**`。
- 落地页相关：`components/landing/**`、`cosmic-*` token。
- `docs/design/` 下既有文档（含 landing/ 目录）。

## P1 —— 允许受限修改（必须回归）

| 文件 | 允许的修改 | 风险与回归 |
|---|---|---|
| `frontend/tailwind.config.js` | 仅替换全部 `dark-*` 颜色值（按 DESIGN_SYSTEM.md），不动 light-*、cosmic-*、字号/间距/圆角 | **全站暗色视觉变化**：必须对 /chat、/documents、/skills、/admin、/login 做暗色截图巡检；亮色主题不受影响；落地页不受影响（cosmic-* 独立） |
| `frontend/src/hooks/useMemory.ts` | 扩展派生数据与本地交互状态（mock 停用覆盖表、筛选状态可放页面）；保持现有请求契约与函数签名向后兼容 | 仅 /memory 使用；聊天页 `InspectorMemory` 不依赖 hook |
| `frontend/src/lib/memory.ts` | 仅**追加**可选字段（`happened_at`、`source_run_id`、`mention_count` 已有等），不改既有字段 | 类型被 `InspectorMemory.tsx` 复用；追加字段不破坏调用方 |
| `frontend/src/components/memory/*` | 视觉重建（列表卡/详情） | 仅 /memory 使用 |

## P2 —— 本次施工范围

- `frontend/src/pages/Memory.tsx`（重写编排）
- `frontend/src/components/memory/` 新组件与 `memory.css`
- `frontend/src/lib/memoryCategories.ts`、`memoryMock.ts`

## 铁律

1. 不改后端、不改 API 契约、不新增依赖。
2. 不扩大修改范围；每阶段 `git diff` 只含清单内文件。
3. 不覆盖用户未提交改动（`Caddyfile`、`deploy.sh`、`runner.py`、`docker-compose.yml`、`ChatInput.tsx` 等）。
4. 旧 `MemoryCard.tsx` / `MemoryInspector.tsx` 在页面切换后若无引用，**保留文件不删除**（skill 纪律），也不得顺手改它。
