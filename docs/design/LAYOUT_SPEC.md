# Onefold 布局与尺寸规范（LAYOUT_SPEC）

> 全部数值直接取自四份设计稿 HTML 的 Tailwind 类；gutter-xs/sm/md/lg/xl = 4/8/16/24/32px，section=48px。
> 断点：lg = 1024px（Tailwind 默认）。根容器 `min-h-[1024px]`，`flex-col lg:flex-row`。

## 1. 三栏宽度

| 区域 | 主工作区 | 专注态 | 检查器展开态 |
|---|---|---|---|
| A 左导航 | 240px（`lg:w-[240px] shrink-0`） | 60px 图标栏 | 224px 紧凑 |
| B 中央 | flex-1 min-w-0 | flex-1 | flex-1 |
| C 检查器 | 320px | 隐藏 | 440px |
| 画布限宽 | max-w-800 mx-auto | max-w-820 | max-w-740 |
| 输入区限宽 | max-w-800 | max-w-820 | max-w-740 |

窄屏（<1024px）：三栏纵向堆叠，导航 border-b、检查器 border-t，均 w-full。设计稿无浮层/遮罩方案。【U1】

## 2. 左导航（240px 完整态）

- 外壳：`flex-col justify-between`，bg-surface-container-low，border-r outline-variant。
- 上块：`p-gutter-md(16) flex-col gap-gutter-md(16)`。
- 品牌行：`justify-between gap-8`；品牌盒 24×24 rounded-sm(6) 描边，内 SVG 14×14；
  文案列 gap-0：Onefold title-md(15/22) + 团队名 label-sm(12/16) truncate；
  收起按钮 `p-1.5(6) rounded-sm`，图标 dock_to_right 16px。
- 新建+检索组：`flex-col gap-4`。
  - 新建研究：`px-8 py-8 rounded(8)`，左 add 16px + label-md，右 ⌘N mono-sm，justify-between。
  - 快速检索：`px-8 py-6 rounded`，search 15px + label-sm，右 ⌘K mono-sm。
- 模块导航：`gap-0.5(2) pt-4 border-t`；条目 `px-8 py-6 rounded gap-8`，图标 16px，label-md；
  知识库/记忆右侧计数 mono-sm tabular-nums。
- 会话分组：外层 `gap-16 pt-4 border-t`；组内 `gap-0.5(2)`；
  组标题 label-sm `px-8 pb-4`；条目 `px-8 py-6 rounded justify-between gap-4`；
  激活圆点 6×6(w-1.5)；未激活标题 `pl-3.5(14)`；时间 mono-sm shrink-0。
- 底部身份：`p-16 border-t justify-between gap-8`；头像 28×28(w-7) rounded-full 描边，字 label-sm；
  姓名 label-md + 角色 label-sm；主题按钮 `p-1.5 rounded-sm` 图标 16px。

## 3. 左导航（60px 图标栏 · 专注态）

- 外壳：`py-16 flex-col items-center justify-between`。
- 上列 `gap-16`：品牌盒 32×32(w-8) rounded-sm，SVG 15×15；
  新建 36×36(w-9) rounded(8) surface 底描边，add 18px 主色；检索 36×36 无框 search 18px；
  分隔线 `w-24 border-t my-4`；模块列 `gap-4`，条目 36×36 rounded，图标 18px。
- 下列 `gap-8`：主题 36×36 图标 17px；头像 28×28。

## 4. 左导航（224px 紧凑态 · 检查器展开）

与完整态同构，差异：品牌无副标题；新建按钮无 ⌘N（`gap-8` 左对齐）；模块无计数；
会话无时间戳（激活项 `gap-8` 圆点+标题）；底部身份为单行 label-sm「姓名 · 角色」+ 主题按钮。

## 5. 中央顶栏

| 状态 | 内边距 | 标题 | 右侧 |
|---|---|---|---|
| 主 | px-32 py-16，flex-wrap justify-between gap-16 | headline-lg text-balance + 元信息行(gap-8, label-sm/mono-sm) | 专注阅读 + 上下文面板 |
| 专注 | px-32 py-16，sticky top-0 z-10 | headline-lg truncate + 徽章(px-8 py-2 rounded-sm) | 展开来源(3) |
| 展开 | px-24 py-16 | headline-lg truncate + mono-sm 对照行(gap-2) | 「检查器已展开」徽章(px-8 py-4) |

- 主态按钮：`px-8 py-6 rounded-sm gap-6` 图标 15px + label-sm；
  专注阅读 = surface 底描边；上下文面板 = container-high 底无描边、图标主色。
- 元信息行：`范围：公共知识库 · 个人知识库 · 临时文档`(label-sm) · `2026-11-24 14:18`(mono-sm) · `3 份参考来源`(mono-sm)。

## 6. 研究画布（主态）

外壳 `max-w-800 mx-auto px-32 py-24 flex-col gap-24`。

- 提问卡：`p-16 rounded-md(12) container 底描边 justify-between gap-16`；正文 body-md text-pretty；时间 mono-sm `pt-4 shrink-0`。
- 检索状态卡：`rounded(8) surface 底描边 px-16 py-8`；summary `py-4 justify-between`：
  左 = 8×8(w-2) 主色圆点 + label-md；右 = mono-sm 统计 + expand_more 16px；
  明细 `mt-8 pt-8 border-t grid sm:grid-cols-2 gap-8`；行 = check_circle 14px + label-sm + 右 mono-sm 耗时。
- 报告 article `gap-24`：
  - 核心结论：`pl-16 border-l-2 主色 flex-col gap-4`；标签 label-sm 强调色；正文 body-md。
  - 章节：`gap-16`；h2 headline-md；p body-md；表格容器 `rounded(8) 描边 surface 底 overflow-x-auto`。
  - 表格：th `px-16 py-8` label-sm variant，thead container-low 底 border-b；td `px-16 py-10`；行 border-b（末行无）。
  - 引用胶囊（内联）：`px-6 py-2 mx-2 rounded-sm gap-4 items-baseline`，container 底描边；范围词 label-sm 强调色 + 文件名 label-sm + 页码 mono-sm。
  - 延伸追问：`flex-wrap gap-8 pt-4`；标签 label-sm outline；chip `px-8 py-4 rounded-sm surface 底描边` label-sm。

## 7. 专注态画布

`max-w-820 px-32 py-32 gap-32`；问题上下文行 `pb-16 border-b justify-between`（body-sm variant + mono-sm）；
执行摘要 `pl-24 border-l-2 gap-8`；章节同主态；footer `pt-16 border-t flex-wrap justify-between gap-8`。

## 8. 展开态画布

`max-w-740 px-24 py-24 gap-24`；核心结论 pl-16；无提问卡/检索卡/chips。

## 9. 输入区

- 主态：外层 `border-t px-32 py-16`；卡片 `max-w-800 rounded-md(12) surface 底描边 p-16 flex-col gap-8`。
  - 顶行 `flex-wrap justify-between gap-8`：附件芯片 `px-8 py-2 rounded-sm container 底描边 gap-6`（临时 label-sm 强调 + 文件名 label-sm + close 13px）；范围按钮 `px-8 py-2 rounded-sm gap-4` tune 14px + label-sm。
  - textarea：rows=2，body-md，无边框无内边距，placeholder outline 色。
  - 底行 `pt-4 border-t justify-between`：左组 `gap-16`（attach_file 16px / alternate_email 16px + label-sm）；
    发送 `px-16 py-6 rounded-sm gap-6` 主色实心，label-md + arrow_upward 15px。
- 专注/展开态：`max-w-820/740 rounded-md surface 底描边 px-16 py-8 flex-row justify-between gap-16`；
  单行 input body-sm；发送 `px-16 py-6 rounded-sm` label-md 无图标。

## 10. 右检查器

- 320px 态：页签 `grid-cols-4 border-b px-8`；tab `py-12 text-center border-b-2` label-md；面板 `p-16 gap-16`。
  - 来源项：`pb-16 border-b gap-6`（末项无 border/pb）；标题行 label-md + mono-sm 相关度；元行 label-sm + mono-sm `gap-8`；摘录 body-sm variant。
  - 记忆项：`gap-4`，mono-sm 日期行 + body-sm；首项 `pb-16 border-b`。
  - 工具行：`py-4 justify-between`，左 mono-sm 工具名，右 mono-sm 主色「已完成 · 0.48s」。
  - 文档行：`py-6 justify-between border-b`（末行无），label-md 文件名 + mono-sm「范围 · Ready」。
- 440px 态：头部 `px-16 py-8 border-b justify-between`；页签 `flex gap-16`，tab `py-4 border-b-2` label-md；close `p-4 rounded-sm` 16px。
  - 预览区 `p-16 border-b surface 底 gap-16`：标题 title-md + 徽章(px-6 py-2 rounded-sm primary-container)；
    mono-sm 元行「第 14 页 · chunk #0412 · 相关度 0.91」；打开原文 `px-8 py-4 rounded-sm container 底描边` label-sm。
  - 段落卡 `p-16 rounded(8) container-low 底描边 gap-8`：头 label-sm + mono-sm；正文 body-sm + mark 高亮；
    翻页行 `pt-4 border-t justify-between` label-sm。
  - 列表区 `p-16 gap-8`：标题 label-sm outline；项 `p-8 rounded(8) justify-between gap-8`，
    选中 = surface 底 + 主色描边，未选中 = 透明描边 + hover:container-high；标题 label-md + 元行 label-sm + mono-sm 相关度。

## 11. 图标尺寸汇总（Material Symbols Outlined）

16px：收起/主题/导航条目/新建 add/expand_more/close；15px：检索 search/顶栏按钮/发送箭头；
14px：检索明细 check_circle/范围 tune；13px：附件芯片 close；18px：图标栏全部；17px：图标栏主题。