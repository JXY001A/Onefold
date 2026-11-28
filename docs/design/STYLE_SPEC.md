# Onefold 视觉样式规范（STYLE_SPEC）

> 亮色 token 取自四份设计稿共用的 tailwind.config；暗色自 2026-11-28 起整组替换为宇宙蓝系（用户确认，全局生效），
> 逐值与依据见 `docs/design/memory-center/DESIGN_SYSTEM.md`，下表已同步为现行值。
> 命名约定：下文 surface/container/outline 等均指 `light-*` / `dark:*` 成对 token。

## 1. 色板（完整 token 表）

| token | 亮色 | 暗色 | 用途 |
|---|---|---|---|
| primary | #648B54 | #668FFF | 主色：图标/圆点/竖线/描边激活/发送底 |
| on-primary | #101315 | #070B16 | 主色实心底上的文字 |
| primary-container | #E4ECE0 | #1A274A | 徽章底/引用激活底/mark 高亮底 |
| on-primary-container | #3B5930 | #9BB8FF | 徽章文字；亮稿强调文字 |
| secondary / on-secondary | #5C655E / #FFFFFF | #9875FF / #070B16 | 备用（稿中未直接使用） |
| warning | #9A6B16 | #E5B869 | 「临时」强调（暗稿） |
| on-warning | #FFFFFF | #070B16 | — |
| warning-container | #F5EFE2 | #262018 | 警示底 |
| on-warning-container | #5C3D06 | #E5B869 | 亮稿「临时」强调文字 |
| success / on-success | #648B54 / #101315 | #62D6E8 / #070B16 | 暗色为蓝青：开启态圆点/开关轨道 |
| error / on-error | #B91C1C / #FFFFFF | #F87171 / #070B16 | 错误 |
| background | #F7F8F6 | #070B16 | 页面/中央区/顶栏/输入区底 |
| on-background | #202522 | #F1F5FF | 页面默认文字 |
| surface | #FFFFFF | #111A2B | 卡片/按钮/输入卡底 |
| surface-container-lowest | #F7F8F6 | #070B16 | 同 background |
| surface-container-low | #F1F3EF | #0B1020 | 左右栏底/表头底/段落卡底 |
| surface-container | #F0F2EE | #152036 | 提问卡底/引用胶囊底/激活会话底(暗) |
| surface-container-high | #E9EDE7 | #1C2A45 | hover 底/激活导航底/头像底(暗)/上下文面板底 |
| surface-container-highest | #E1E6DF | #243556 | 备用 |
| on-surface | #202522 | #F1F5FF | 标题/正文/激活文字 |
| on-surface-variant | #5C655E | #A3AEC4 | 次要正文/未激活导航/摘录 |
| outline | #666F68 | #7C8CA8 | 弱文字：时间/计数/组标题/placeholder |
| outline-variant | #E5E9E3 | #1E2C47 | 所有描边/分隔线 |

## 2. 字体与字号

字体族：headline/title = Inter；body/label = Noto Sans SC；mono = IBM Plex Mono。
Google Fonts 权重：Inter 400/500/600，Noto Sans SC 400/500/600，IBM Plex Mono 400/500。
Material Symbols Outlined：`wght,FILL@100..700,0..1&display=block`；
基础 CSS：`display:inline-block; width/height:1em; line-height:1!important; box-sizing:content-box; overflow:hidden; vertical-align:middle`。

| token | 字号/行高 | 字距 | 字重 | 典型用途 |
|---|---|---|---|---|
| headline-lg | 24/32 | -0.4px | 600 | 顶栏研究标题 |
| headline-md | 18/26 | -0.2px | 600 | 报告章节 h2 |
| title-md | 15/22 | 0 | 500 | 品牌名/来源预览标题 |
| body-md | 15/27 | 0 | 400 | 提问/报告正文/主输入框 |
| body-sm | 14/22 | 0 | 400 | 摘录/记忆/专注输入/空态说明 |
| label-lg | 14/20 | 0 | 500 | （稿中未用） |
| label-md | 13/18 | 0 | 500 | 导航/按钮/页签/来源标题 |
| label-sm | 12/16 | 0 | 400 | 组标题/元信息/徽章/chip |
| mono-sm | 12/16 | 0 | 400 | 时间/计数/相关度/工具名/快捷键 |

数字一律 `tabular-nums`；正文段落 `text-pretty`，主态标题 `text-balance`。

## 3. 强调文字规则（亮暗差异，重要）

暗稿：强调文字 = primary / warning。
亮稿：强调文字 = on-primary-container(#3B5930) / on-warning-container(#5C3D06)。
适用位置：核心结论/执行摘要标签、引用胶囊范围词（公共/临时）、表格主数值、来源相关度分值、附件芯片「临时」。
「个人」范围词两稿均为 on-surface-variant。
实现建议：统一用 `text-light-on-primary-container dark:text-dark-primary` 等成对类。

## 4. 圆角 / 描边 / 阴影

- 圆角：sm=6px（小按钮/徽章/胶囊/品牌盒）、DEFAULT=8px（导航条目/卡片/表格容器/图标栏按钮）、md=12px（提问卡/输入卡）、lg=16px（稿中未用）、full（头像/圆点）。
- 描边：统一 1px outline-variant；激活态描边 = primary（选中来源项/输入 focus-within/引用激活胶囊）。
- 分隔：border-t/border-b 1px outline-variant；核心结论/执行摘要为 border-l-2 primary。
- 阴影：四份设计稿均无 box-shadow。现有实现的 shadow-2xl（窄屏浮层）属外加。【U1】
- 渐变：无。背景全部纯色。

## 5. 状态样式

| 状态 | 规则 |
|---|---|
| hover（ghost 按钮/导航/会话） | bg-container-high；文字 variant→on-surface |
| hover（surface 描边按钮） | bg-container-high（新建）或仅文字变深（顶栏专注阅读） |
| hover（主色实心发送） | opacity-90 |
| 激活导航 | bg-container-high + text-on-surface + 图标 primary |
| 激活会话（暗） | bg-container + 6px primary 圆点 |
| 激活会话（亮） | bg-surface + border outline-variant + 圆点 |
| 激活页签 | border-b-2 primary + text-on-surface（320 态文字非主色） |
| 未激活页签 | border-transparent + text-outline + hover:text-on-surface |
| focus-visible | outline-2 primary（新建/发送 offset-2） |
| focus-within（输入卡） | border-primary |
| 选中来源项 | bg-surface + border-primary |
| 引用激活胶囊 | bg-primary-container + border-primary + 全文 primary |
| mark 高亮 | bg-primary-container + text-on-surface + px-1 rounded-sm |
| 过渡 | transition-colors/opacity，120ms ease-out（duration-state-change） |
| details 展开 | expand_more rotate-180（120ms） |

## 6. 全局基础样式（设计稿 <style>）

- `details summary::-webkit-details-marker { display:none }`（主稿）。
- `[hidden] { display:none !important }`。
- body：bg-background + text-on-background + font-body + antialiased。
- 设计稿未定义滚动条样式；现有自定义滚动条（--of-scrollbar）为外加项。【U1】

## 7. 报告排版（Markdown → 设计稿映射）

设计稿报告是语义化编辑排版，不是通用 Markdown 渲染：
- 核心结论/执行摘要 = 左竖线引导段（非 Markdown 元素，需组件化或约定 Markdown 首段）。
- h2 = headline-md（18/26 600 Inter），章节间距 gap-16，报告块间距 gap-24。
- 正文 body-md 15/27；strong = font-semibold。
- 表格 = surface 底圆角容器 + container-low 表头 + label-sm 表头字 + mono-sm 数值。
- 现有 markdown.css 的 h1/h2/h3、p、table  margins/字号与设计稿不一致，需按本表重写。
- 引用胶囊为内联元素，需 Markdown 内嵌组件（现后端无引用数据【U6】）。

## 8. 用户消息气泡（用户变更，2026-11-28，覆盖 2.0 设计稿的通栏提问卡）

- 普通对话的用户消息改为**右对齐全圆胶囊**：外层 `flex justify-end`，气泡 `max-w-[80%] rounded-full px-gutter-lg py-gutter-sm`。
- 底色用主题淡色容器：亮色 `light-primary-container` + `light-on-primary-container` 文字；暗色 `dark-primary-container` + `dark-on-primary-container` 文字（用户反馈主色过深后调整为柔和版，2026-11-28）。
- 专注阅读模式的「研究问题」上下文行、检查器展开态的隐藏逻辑保持不变。
- 目的：明确区分用户与助手（助手仍为无气泡的编辑式排版）。
- 依据：用户以聊天界面参考图指定。