# 落地页设计规范（The Neural Universe）

> 从 HTML + Figma 节点提取，全部为设计稿原值，不得凭审美补全。
> 落地页固定深色，不参与双主题体系。

## 1. 色板（接入方式：tailwind.config 新增 `cosmic` 色组）

| Token | 值 | 用途 |
|---|---|---|
| `cosmic.bg` | `#070B16` | 页面底色 |
| `cosmic.surface` | `#0B1020` | 次级区块底（能力区 40% / 入口区 50% 叠加） |
| `cosmic.card` | `#111A2B` | 卡片、按钮次级底、插图面板 |
| `cosmic.primary` | `#668FFF` | 主色：眉题、描边、链接强调 |
| `cosmic.electric` | `#568BFF` | 主按钮渐变左端、径向光晕 |
| `cosmic.purple` | `#9875FF` | 次强调：Agent 卡、悬停描边 |
| `cosmic.cyan` | `#62D6E8` | 状态点、成功/第三强调 |
| `cosmic.text` | `#F1F5FF` | 主文字 |
| `cosmic.secondary` | `#A3AEC4` | 次级文字、body |
| `cosmic.muted` | `#7C8CA8` | 弱文字、序号、注释 |

白色叠加：区块分隔线 `white/6%`、插图面板描边 `white/5%`；选中文本 `primary/30`。

## 2. 效果类（独立 `landing.css`，限定在落地页根节点作用域内）

- **环境底光**（fixed 全屏层）：`radial-gradient(ellipse 68% 54% at 72% 38%, rgba(102,143,255,.14) 0, rgba(152,117,255,.08) 42%, transparent 74%)` + `radial-gradient(ellipse 46% 42% at 22% 18%, rgba(98,214,232,.06) 0, transparent 65%)`。
- **卡片**：渐变底 `linear-gradient(160deg, rgba(17,26,43,.88), rgba(11,16,32,.94))`；描边 `1px rgba(102,143,255,.16)`；阴影 `0 20px 50px rgba(3,6,14,.55), inset 0 1px 0 rgba(241,245,255,.05)`；悬停 `translateY(-3px)`、描边 `rgba(152,117,255,.38)`、阴影 `0 26px 60px rgba(5,10,24,.72), 0 0 36px rgba(102,143,255,.14), inset 0 1px 0 rgba(241,245,255,.08)`；过渡 `0.35s cubic-bezier(.22,1,.36,1)`。
- **主按钮**：渐变 `linear-gradient(135deg,#3964E6,#4E67F2 50%,#7A52E6)`；阴影 `0 8px 28px rgba(57,100,230,.32), inset 0 1px 0 rgba(255,255,255,.22)`；悬停 `translateY(-1px) brightness(1.07)` 阴影加深；按下回落。
- **次按钮**：底 `card/48%`、描边 `rgba(163,174,196,.22)`、`backdrop-filter: blur(8px)`；悬停底 `primary/12%`、描边 `primary/45%`、`translateY(-1px)`。
- **光晕呼吸**：`pulseSlow 6s ease-in-out infinite`（Hero 右侧体积光）。
- 未定义的 `.reveal-section` 不实现。

## 3. 字体与字号（字体项目已加载，无需改动 index.html）

Inter（拉丁）/ Noto Sans SC（中文）/ IBM Plex Mono（眉题·序号·数据）。

| 角色 | 规格 |
|---|---|
| H1 | 38 → 46 → 52px（sm/lg），600，行高 1.12，字距 -0.02em；「智能的边界」为 text→primary→purple 渐变字 |
| H2 | 28 → 38px（能力区/工作区）；入口区 30 → 40px，600，tracking-tight |
| H3 | 22px，600 |
| 正文 | 14px / 1.7（卡片内）；16px / 1.65（区块引导语）；Hero 16 → 17px / 1.7 |
| 眉题 | mono 11px，tracking-widest，大写 |
| 卡片标签 | mono 12px tracking-wider（Research=cyan / Agents=purple / Experiments=primary） |
| 序号 | mono 11px（01/02/03），muted |
| 按钮 | 15px medium |
| 注释 | 12px muted |

## 4. 间距 / 圆角 / 断点

- 区块垂直：`py-20 lg:py-28`；Hero `pt-12 pb-20 lg:pt-20 lg:pb-28`。
- 圆角：胶囊 9999、卡片 16px（rounded-2xl）、插图面板 12px（rounded-xl）、按钮 8px（rounded-lg）、序号块 6px（rounded-md）。
- 断点：沿用默认 sm 640 / lg 1024；设计稿基准视口 1440×1024。

## 5. 图标

Material Symbols Outlined，全部由文案语义驱动（arrow_forward 用于主 CTA）；尺寸 18px（按钮内）。无其他图标体系。
