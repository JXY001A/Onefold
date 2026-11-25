# Onefold 设计逆向工程总览

> 依据：`~/Downloads/onefold_2.0_main_workspace_dark_mode.html`（主稿·暗）、
> `onefold_2.0_main_workspace_light_mode.html`（主稿·亮）、`onefold_2.0_focus_mode.html`（专注态）、
> `onefold_2.0_expanded_source_inspector.html`（检查器展开态）。四份均为 Tailwind CDN + 同一份 token 配置。
> 本文档只记录设计稿事实；尺寸见 LAYOUT_SPEC.md，颜色/字体见 STYLE_SPEC.md，组件映射见 COMPONENT_MAPPING.md。

## 1. 页面整体结构

单页三栏，根容器 `min-h-[1024px] w-full flex flex-col lg:flex-row`（≥1024px 横向三栏，窄屏纵向堆叠）：

```
body (bg-background, font-body, antialiased)
└─ 根容器 flex
   ├─ A 左导航 aside（bg-surface-container-low，border-r）
   │   ├─ 上块 p-16 flex-col gap-16
   │   │   ├─ 品牌行：24px 盒装六边形 SVG + Onefold(title-md) + 团队名(label-sm) ｜ 收起按钮(dock_to_right)
   │   │   ├─ 新建研究（surface 底 + 描边按钮，add 主色图标，右侧 ⌘N）
   │   │   ├─ 快速检索（无框 ghost，右侧 ⌘K）
   │   │   ├─ 模块导航（border-t + pt-4，gap-2）：研究对话 / 知识库(计数5) / 研究记忆(计数4)
   │   │   └─ 会话分组（border-t + pt-4）：今天 / 本周 / 更早
   │   └─ 底部身份区 p-16 border-t：28px 圆形头像 + 姓名/角色 ｜ 主题切换
   ├─ B 中央工作区 main（flex-1，bg-background，flex-col justify-between）
   │   ├─ 顶栏 header（border-b，px-32 py-16）：headline-lg 标题 + 元信息行 ｜ 专注阅读 / 上下文面板
   │   ├─ 研究画布（max-w-800 居中，px-32 py-24，gap-24）
   │   │   ├─ 用户提问卡片（container 底，rounded-12，p-16，右侧 mono 时间）
   │   │   ├─ 检索状态卡（surface 底，rounded-8，details 可折叠，2 列明细）
   │   │   └─ 研究报告 article（gap-24）
   │   │       ├─ 核心结论（左 2px 主色竖线 + pl-16）
   │   │       ├─ 章节 section（gap-16：headline-md 标题 + body-md 段落 + 内联引用胶囊 + 数据表格）
   │   │       └─ 延伸追问 chips
   │   └─ 输入区（border-t，px-32 py-16，内层 max-w-800）
   │       └─ 输入卡片（surface 底 rounded-12 p-16，focus-within 主色描边）
   │           ├─ 顶行：附件芯片(临时·文件名·×) ｜ 范围按钮(tune)
   │           ├─ textarea rows=2（body-md）
   │           └─ 底行 border-t pt-4：附加文档 / 引用知识库 ｜ 发送(主色实心)
   └─ C 右检查器 aside（bg-surface-container-low，border-l）
       ├─ 320px 态：顶部直接 4 页签（来源/记忆/工具/文档，grid-cols-4）
       └─ 440px 态：页签行(来源详情(3)/记忆/工具/文档 + close) → 命中来源预览 → 全部命中来源列表
```

## 2. 四个设计状态

| 状态 | 左导航 | 中央画布 | 右检查器 | 顶栏 |
|---|---|---|---|---|
| 主工作区 | 240px 完整 | max-w-800，px-32 py-24，gap-24 | 320px，4 页签 | 非 sticky；标题+元信息行；专注阅读/上下文面板 |
| 专注阅读 | 60px 图标栏 | max-w-820，px-32 py-32，gap-32；纯报告（无提问卡/检索卡/chips） | 隐藏 | sticky top-0 z-10；标题 truncate + 「专注阅读模式」徽章；展开来源(3) |
| 检查器展开 | 224px 紧凑（无团队名/⌘N/计数/时间戳） | max-w-740，px-24 py-24，gap-24 | 440px，来源详情+预览+列表 | px-24；标题 truncate + mono「正在对照来源…」；「检查器已展开」徽章 |
| 亮色主题 | 同结构 | 同结构 | 同结构 | 强调文字改用 on-*-container 深色（见 STYLE_SPEC §3） |

专注态报告额外元素：顶部「研究问题：…」上下文行（body-sm variant + mono 耗时，border-b）、
执行摘要（pl-24）、文末引用汇总 footer（border-t + 「在来源检查器中对照原文 →」链接）。
专注态与展开态输入区均为单行紧凑式：input(body-sm) + 发送（无图标）。

## 3. 可识别的交互状态（设计稿内明示）

- 主题切换：`#theme-toggle` 切换 `html.dark`；暗稿图标 light_mode，亮稿图标 dark_mode。
- 检查器页签：click 切换 aria-selected/tabindex；激活 = border-b-2 主色 + on-surface 文字；未激活 = border-transparent + outline 文字 + hover:on-surface；面板用 hidden 切换。
- 检索状态：`<details open>` 原生折叠；expand_more 随 group-open 旋转 180°；summary 隐藏原生 marker。
- 会话项：激活 = container 底（亮稿另加 outline-variant 描边）+ 1.5px 主色圆点；未激活 = variant 文字 + hover:container-high，标题 pl-14 对齐（无圆点）。
- 模块导航：激活 = container-high 底 + on-surface 文字 + 主色图标；未激活 hover 同上。
- 新建研究：hover:container-high；focus-visible:outline-2 主色。
- 引用胶囊：主稿为 button（data-citation-target 指向来源 id），hover:container-high；展开稿中命中项为激活态 = primary-container 底 + 主色描边 + 全文主色；专注稿为 span（不可点）。
- 发送按钮：hover:opacity-90；focus-visible:outline-2 offset-2 主色。
- 输入卡片：focus-within 描边变主色。
- 展开态来源列表：选中项 = surface 底 + 主色描边；其余 = 透明描边 + hover:container-high。
- 来源预览：mark 高亮 = primary-container 底 + rounded-sm px-1；上一页/下一页按钮 hover:on-surface。
- 设计稿未定义：加载态、空态、错误态、禁用态、toast、滚动条样式、窄屏浮层/遮罩。【不确定项 U1】

## 4. 亮暗稿差异（除 html.class 外的真实差异）

1. 强调文字 token：暗稿用 primary/warning；亮稿用 on-primary-container(#3B5930)/on-warning-container(#5C3D06)。
   涉及：核心结论标签、引用胶囊范围词、表格主数值、来源相关度、附件芯片「临时」。
2. 品牌盒底色：暗稿 surface-container；亮稿 surface（白）。
3. 激活会话项：亮稿多一层 outline-variant 描边且底色 surface；暗稿 container 底无描边。
4. 头像底色：暗稿 container-high；亮稿 surface。
5. 主题按钮图标随主题互换（light_mode ↔ dark_mode）。

## 5. 不确定项登记（不允许猜测，待确认）

- U1：加载/空/错误/禁用态、toast、滚动条、窄屏行为设计稿未给出 → 沿用现有实现或按 token 体系推导，需用户确认。
- U2：品牌副标题设计稿为「检索工程团队」（团队名）；现有数据模型无团队字段 → 显示什么待确认。
- U3：会话分组设计稿为「今天 / 本周 / 更早」；「本周」的边界（自然周 or 近7天）未定义。
- U4：导航计数（知识库5/记忆4）与顶栏「3 份参考来源」「范围：…」的数据来源：计数可由现有 API 得出；参考来源数依赖引用能力（后端缺失）。
- U5：工具耗时（0.48s 等）：现有 ToolRun 无 duration 字段，SSE 未下发 → 缺失。
- U6：引用胶囊/来源相关度/页码/chunk 号/原文预览：后端无 citation 事件、agent 未接 RAG 工具 → 全部缺失。
- U7：224px 紧凑导航是否作为「检查器展开」的联动形态实现，还是仅按 240/60 两态处理。
- U8：设计稿无 Skill/后台入口、无退出登录；现有业务需要保留 → 按现有 nav.ts 追加，样式对齐设计稿条目。