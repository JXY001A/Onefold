# 项目现状审计（记忆中心改版前置）

> 基于只读审计（2026-11-28）。目标页面：/memory。

## 1. 前端现状

| 文件 | 行数 | 职责 |
|---|---|---|
| `src/pages/Memory.tsx` | 95 | 页面编排：分类 tab（按 category 派生计数）、按 updated_at 倒序合并 cards+notes、头部（新增记忆为 Soon 禁用 / 全局开关 / 清空）、关闭警示条、右栏 Inspector |
| `src/components/memory/MemoryCard.tsx` | 67 | 列表卡片：category Badge、类型+更新时间、`提到 N 次`、pinned、正文、编辑/删除 |
| `src/components/memory/MemoryInspector.tsx` | 42 | 详情：category·key、全局启停与 mention_count、类型、updated_at；无来源/引用 |
| `src/hooks/useMemory.ts` | 73 | 挂载 fetch 一次（无轮询）；`toggle/edit(window.prompt)/remove/clearAll` 均 confirm/prompt 原生；无创建/导出 |
| `src/lib/memory.ts` | 52 | `MemoryItem` 类型（缺 status/created_at/usage_count/last_used_at/source_message_id）与 5 个请求封装 |
| `src/components/chat/InspectorMemory.tsx` | 26 | 聊天页内嵌只读记忆列表（复用 MemoryItem 类型，**改类型需保护**） |

无前端测试框架；`PageWorkspace/PageHeader/Tabs` 等共享组件 `components/ui/kit.tsx` 被多页使用。

## 2. 后端真实能力（`/api/memory`）

- `GET /api/memory` → `{enabled, cards[], notes[]}`；仅 `status=active`；序列化字段：`id/kind/category/key/value/text/confidence/mention_count/pinned/source_run_id/happened_at/updated_at`。
- `PATCH /api/memory/settings {enabled}` —— 全局开关（真实）。
- `PATCH /api/memory/{id} {text?, value?, pinned?}` —— 编辑正文（真实；card text 截 120 / note 300 字符）。
- `DELETE /api/memory/{id}`、`DELETE /api/memory` —— 软删除单条 / 清空（真实）。
- 不存在：创建、导出、单条停用状态、引用次数/引用记录 API、统计 API、搜索/筛选/排序参数。
- 模型字段（`models/memory.py`）：`kind(card|note)`、`category`（后端 13 类）、`mention_count`、`usage_count`、`last_used_at`、`last_mentioned_at`、`pinned`、`status(active|deleted)`、`created_at/updated_at`、`source_run_id/source_message_id`。其中 `usage_count/last_used_at/last_mentioned_at/created_at` **有库值但不经 API 返回**。

## 3. 后端分类（13 类，`services/memory_categories.py`）

身份 / 职业 / 教育 / 技能 / 项目 / 目标 / 偏好 / 沟通 / 习惯 / 关系 / 约束 / 兴趣 / 其他。

## 4. 共享与影响面

- 全局换暗色（`tailwind.config.js` dark-* 值替换）→ 所有页面暗色视觉都变化，必须全站回归；light-* 不动，亮色主题页面不受影响。
- `lib/memory.ts` 类型被聊天页 `InspectorMemory.tsx` 复用 → 只允许向后兼容的字段追加。
- 落地页使用独立的 `cosmic-*` 色组，不受 dark-* 替换影响。
- 仓库当前有用户未提交改动（`Caddyfile`、`deploy.sh`、`runner.py` 等）→ 施工范围不触碰。

## 5. 测试基线

- 后端：`test_memory_api.py`（1 例）、`test_memory_service.py`（4 例）、`test_memory_worker.py`（6 例）——本次不改后端，作为回归基线。
- 前端：无测试框架；验收依赖真实运行截图（Playwright/无头 Chrome）。
