# 记忆中心设计规范

> 从设计稿 HTML（内嵌 Tailwind 配置）提取；实现时必须逐值一致。
> 两套色板：`light-*` 保持项目现值；`dark-*` 整组替换为宇宙蓝系（全局生效，用户已确认）。

## 1. 色板（替换 `tailwind.config.js` 中全部 dark-* 值）

| Token | 设计稿值 |
|---|---|
| dark-primary | `#668FFF` |
| dark-on-primary | `#070B16` |
| dark-primary-container | `#1A274A` |
| dark-on-primary-container | `#9BB8FF` |
| dark-secondary | `#9875FF` |
| dark-on-secondary | `#070B16` |
| dark-warning | `#E5B869` |
| dark-on-warning | `#070B16` |
| dark-warning-container | `#262018` |
| dark-on-warning-container | `#E5B869` |
| dark-success | `#62D6E8` |
| dark-on-success | `#070B16` |
| dark-error | `#F87171` |
| dark-on-error | `#070B16` |
| dark-background | `#070B16` |
| dark-on-background | `#F1F5FF` |
| dark-surface | `#111A2B` |
| dark-surface-container-lowest | `#070B16` |
| dark-surface-container-low | `#0B1020` |
| dark-surface-container | `#152036` |
| dark-surface-container-high | `#1C2A45` |
| dark-surface-container-highest | `#243556` |
| dark-on-surface | `#F1F5FF` |
| dark-on-surface-variant | `#A3AEC4` |
| dark-outline | `#7C8CA8` |
| dark-outline-variant | `#1E2C47` |

`light-*` 26 个 token 保持现项目值，不动。

## 2. 字号/字体（沿用项目既有字体栈与字号 token，设计稿一致）

headline-lg 24/32 600 Inter（页面标题与统计数字）；headline-md 18/26 600（弹窗标题）；title-md 15/22 500（详情标题）；body-md 15/27；body-sm 14/22；label-lg 14/20 500；label-md 13/18 500；label-sm 12/16；mono-sm 12/16 IBM Plex Mono（时间戳/计数字段一律 `tabular-nums`）。统计数字使用 headline-lg + tabular-nums。

## 3. 圆角 / 间距

圆角：6（sm）/ 8（默认）/ 12（md）/ 16（lg）/ 9999（full）——与项目一致。间距 token：gutter-xs 4 / sm 8 / md 16 / lg 24 / xl 32 / section 48 / page-margin 24。

## 4. 组件静态样式要点

- **全局开关**：轨道 36×20 rounded-full，开 = `bg-dark-success` + 旋钮 14px `translate-x-[18px] bg-dark-on-success`；关 = `bg-dark-surface-container-highest` + `translate-x-[3px] bg-dark-on-surface-variant`；过渡 `duration-state-change（120ms ease-out）`。
- **状态徽章**：`记忆已开启` pill = `bg-dark-primary-container text-dark-on-primary-container` + 6px 圆点 `bg-dark-success`；关闭态 = `bg-dark-surface-container text-dark-outline`。
- **统计卡**：`bg-dark-surface border-dark-outline-variant rounded`，右侧 32×32 `rounded-sm` 图标盒：全部=dSurfaceContainer/dOutline、已激活=dPrimaryContainer + `text-dark-success`、已停用=dSurfaceContainer + dOutline、累计引用=dPrimaryContainer + `text-dark-primary`。
- **分类 pill**：激活 `bg-dark-primary-container text-dark-on-primary-container`，未激活 `bg-dark-surface text-dark-on-surface-variant hover:bg-dark-surface-container`。
- **列表卡片**：选中 `bg-dark-surface-container border-dark-primary`，未选 `bg-dark-surface border-dark-outline-variant hover:bg-dark-surface-container`；全局关闭时整卡 `opacity-75`；正文 `line-clamp-2`。
- **详情区**：`bg-dark-surface`，属性网格 2 列、行间分隔 `border-y dark-outline-variant`；引用记录条目 `bg-dark-surface-container-low rounded border`。
- **弹窗**：遮罩 `bg-dark-background/80`；编辑弹窗 `max-w-[540px] rounded-lg`；确认弹窗 `max-w-[440px]`；确认按钮 `bg-dark-error text-dark-on-error`。
- **Toast**：复用项目现有 `ToastContext`（设计稿的右下角样式由现有 toast 承担，不另建一套）。
- **滚动条**：列表容器自定义 6px 宽、thumb `#1E2C47`、hover `#243556`（页面级 CSS，作用域限定）。

## 5. 交互状态（设计稿明确）

hover（卡片/按钮/链接）、active、focus-visible（`outline-2 outline-offset-2 outline-dark-primary`，主要可交互元素均定义）、禁用/空态（空列表插画式空态文案「当前筛选条件下暂无记忆」、详情空态「选择一条记忆，查看详细信息」）、全局关闭横幅、弹窗/toast 出现消失。未定义状态：加载骨架、请求失败 —— 保持项目现有 toast 错误提示方式，不新造视觉。
