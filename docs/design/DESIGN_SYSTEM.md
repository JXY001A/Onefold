# Onefold 2.0 设计系统（DESIGN_SYSTEM）

> 整合自四份设计稿 HTML（主工作区亮/暗、专注态、检查器展开态）与已确认的 STYLE_SPEC / LAYOUT_SPEC。
> 实施依据：用户提供的《Onefold 2.0 UI 改版总实施方案（Final Execution Brief）》为最高优先级；本文件与其冲突时以总方案为准，未定义项明确标注「未定义」，不做推测。token 层与 frontend/tailwind.config.js 完全一致，**不重建**。
> 适用范围：主工作区、专注态、320px 检查器、440px 展开检查器、亮/暗主题。其余页面无新设计稿，保持现状。
> 与旧规范冲突时以本文件为准：STYLE_SPEC 旧版的阴影/滚动条与核心结论识别表述已被本文件 §7、§12 与已确认决议取代（不改旧文件，仅声明优先级）。
> 命名约定：下文颜色均指 `light-*` 与 `dark:*` 成对 token；gutter-xs/sm/md/lg/xl = 4/8/16/24/32px。

## 1. 色彩系统（亮 / 暗）

| token | 亮色 | 暗色 | 用途 |
|---|---|---|---|
| primary | #648B54 | #B6E3A1 | 图标/圆点/竖线/激活描边/发送底 |
| on-primary | #101315 | #101315 | 主色实心底上的文字 |
| primary-container | #E4ECE0 | #1E2A1B | 徽章底/引用激活底/mark 高亮底 |
| on-primary-container | #3B5930 | #B6E3A1 | 徽章文字；亮稿强调文字 |
| secondary / on-secondary | #5C655E / #FFFFFF | #929BA1 / #101315 | 备用（稿中未直接使用） |
| warning / on-warning | #9A6B16 / #FFFFFF | #D6B36A / #101315 | 「临时」强调（暗稿用 warning） |
| warning-container | #F5EFE2 | #282216 | 警示底 |
| on-warning-container | #5C3D06 | #D6B36A | 亮稿「临时」强调文字 |
| success / on-success | #648B54 / #101315 | #B6E3A1 / #101315 | 同主色 |
| error / on-error | #B91C1C / #FFFFFF | #F87171 / #101315 | 错误 |
| background / on-background | #F7F8F6 / #202522 | #101315 / #E9ECEE | 页面/中央区/顶栏/输入区底与默认文字 |
| surface | #FFFFFF | #171C1F | 卡片/按钮/输入卡底 |
| surface-container-lowest | #F7F8F6 | #101315 | 同 background |
| surface-container-low | #F1F3EF | #14191B | 左右栏底/表头底/段落卡底 |
| surface-container | #F0F2EE | #1D2427 | 提问卡底/引用胶囊底/激活会话底(暗) |
| surface-container-high | #E9EDE7 | #252D30 | hover 底/激活导航底/头像底(暗)/上下文面板底 |
| surface-container-highest | #E1E6DF | #2E373B | 备用 |
| on-surface | #202522 | #E9ECEE | 标题/正文/激活文字 |
| on-surface-variant | #5C655E | #929BA1 | 次要正文/未激活导航/摘录 |
| outline | #666F68 | #808B92 | 弱文字：时间/计数/组标题/placeholder |
| outline-variant | #E5E9E3 | #2A3235 | 所有描边/分隔线 |

**强调文字亮暗差异（重要）**：暗稿强调文字 = primary / warning；亮稿 = on-primary-container / on-warning-container。
适用：核心结论与执行摘要标签、引用胶囊范围词（公共/临时）、表格主数值、来源相关度、「临时」芯片。
「个人」范围词两稿均为 on-surface-variant。实现统一写成 `text-light-on-primary-container dark:text-dark-primary` 等成对类。
其他亮暗差异：品牌盒底亮=surface、暗=container；激活会话亮=surface+描边、暗=container 无描边；头像底亮=surface、暗=container-high；主题图标亮稿=light_mode、暗稿=dark_mode。

## 2. 字体与字重

- headline / title = Inter（400/500/600）；body / label = Noto Sans SC（400/500/600）；mono = IBM Plex Mono（400/500）。
- 数字一律 `tabular-nums`；正文段落 `text-pretty`；主态顶栏标题 `text-balance`。
- 字体经 Google Fonts CDN 加载；加载失败时图标退化为连字文本（已知风险，见 PROJECT_AUDIT §6.4）。

## 3. 字号 / 行高 / 字距

| token | 字号/行高(px) | 字距 | 字重 | 典型用途 |
|---|---|---|---|---|
| headline-lg | 24/32 | -0.4px | 600 | 顶栏研究标题 |
| headline-md | 18/26 | -0.2px | 600 | 报告章节 h2 |
| title-md | 15/22 | 0 | 500 | 品牌名/来源预览标题 |
| body-md | 15/27 | 0 | 400 | 提问/报告正文/主输入框 |
| body-sm | 14/22 | 0 | 400 | 摘录/记忆/专注输入/空态说明 |
| label-lg | 14/20 | 0 | 500 | 稿中未用（现有工具卡在用，改造后移除） |
| label-md | 13/18 | 0 | 500 | 导航/按钮/页签/来源标题 |
| label-sm | 12/16 | 0 | 400 | 组标题/元信息/徽章/chip |
| mono-sm | 12/16 | 0 | 400 | 时间/计数/相关度/工具名/快捷键 |

## 4. 间距系统

gutter-xs=4 / sm=8 / md=16 / lg=24 / xl=32 / section=48 / page-margin=24。
常用组合：画布主态 px-32 py-24 gap-24；专注态 px-32 py-32 gap-32；展开态 px-24 py-24 gap-24；
导航上块 p-16 gap-16；组内条目 gap-0.5(2px)；组间 gap-16 pt-4 border-t。

## 5. 圆角

sm=6px（小按钮/徽章/胶囊/品牌盒）；DEFAULT=8px（导航条目/卡片/表格容器/图标栏按钮）；
md=12px（提问卡/输入卡）；lg=16px（稿中未用）；full（头像/圆点）。

## 6. 边框与分隔线

- 描边统一 1px outline-variant；激活描边 = primary（选中来源项/输入 focus-within/引用激活胶囊）。
- 分隔：border-t / border-b 1px outline-variant；核心结论与执行摘要为 border-l-2 primary。
- 窄屏堆叠时：导航 border-b、检查器 border-t（均 w-full）。

## 7. 阴影与渐变限制

四份设计稿**均无 box-shadow、无渐变**，背景全部纯色。
**不设「全项目无 box-shadow」规则**。仅清理本轮实际改造范围内、设计稿明确不存在的额外阴影（如 320 检查器窄屏浮层随堆叠方案移除，其 shadow-2xl 一并消失）。
ToolDrawer、Soon 等设计稿未定义的业务追加组件**单独评估，不自动全局修改**；默认保留现状，如需调整须单独确认并验证未设计页面视觉不变。
共享组件不得因本轮改造影响未设计页面；未设计页面一律保持现状。
自定义滚动条设计稿未定义，**保留现有实现**（C7）。

## 8. 交互状态（hover / active / focus / disabled）

| 状态 | 规则 |
|---|---|
| hover（ghost 按钮/导航/会话） | bg-container-high；文字 variant→on-surface |
| hover（surface 描边按钮） | bg-container-high（新建）或仅文字变深（顶栏专注阅读） |
| hover（主色实心发送） | opacity-90 |
| 激活导航 | bg-container-high + text-on-surface + 图标 primary |
| 激活会话 | 暗=bg-container+6px 主色圆点；亮=bg-surface+outline-variant 描边+圆点 |
| 激活页签 | border-b-2 primary + text-on-surface（320 态文字非主色） |
| 未激活页签 | border-transparent + text-outline + hover:text-on-surface |
| focus-visible | outline-2 primary（新建/发送 offset-2）；现实现为 0 处，需补 |
| focus-within（输入卡） | border-primary |
| 选中来源项 | bg-surface + border-primary |
| 引用激活胶囊 | bg-primary-container + border-primary + 全文 primary |
| mark 高亮 | bg-primary-container + text-on-surface + px-1 rounded-sm |
| disabled | 设计稿**未定义全局 disabled 视觉规范**；Soon 的 opacity/saturate/禁点/提示仅是现有占位功能的实现方式，**不得上升为全局 disabled 设计规范** |
| 过渡 | transition-colors/opacity，120ms ease-out（duration-state-change）；details 展开 expand_more rotate-180 |

全局基础：`details summary::-webkit-details-marker{display:none}`；`[hidden]{display:none!important}`；
body = bg-background + text-on-background + font-body + antialiased。滚动条样式设计稿**未定义**：现有自定义滚动条样式按 C7 确定保留。

## 9. 图标字体与尺寸

Material Symbols Outlined，`wght,FILL@100..700,0..1&display=block`；
基础 CSS：`display:inline-block; width/height:1em; line-height:1!important; box-sizing:content-box; overflow:hidden; vertical-align:middle`。
尺寸：16px=收起/主题/导航条目/新建 add/expand_more/close；15px=检索 search/顶栏按钮/发送箭头；
14px=检索明细 check_circle/范围 tune；13px=附件芯片 close；18px=图标栏全部；17px=图标栏主题。
现有 Icon.tsx 用内联 style fontSize 传尺寸（非 className 裸值），沿用该约定。

## 10. 三种布局状态

断点 lg=1024px；根容器 `min-h-[1024px] flex flex-col lg:flex-row`；**窄屏三栏纵向堆叠，设计稿无浮层/遮罩/抽屉方案**。

| 区域 | 主工作区 | 专注态 | 检查器展开态 |
|---|---|---|---|
| 左导航 | 240px 完整 | 60px 图标栏 | 224px 紧凑 |
| 中央 | flex-1 min-w-0 | flex-1 | flex-1 |
| 右检查器 | 320px | 隐藏 | 440px |
| 画布/输入限宽 | max-w-800 | max-w-820 | max-w-740 |

## 11. 工作区 / 专注 / 检查器布局规格

- **导航 240**：bg-container-low border-r；品牌盒 24×24 rounded-sm 内 SVG 14×14 + Onefold title-md + 副标题 label-sm（暂定「研究工作区」，不代表真实团队名称，C4）；收起按钮 p-1.5 图标 dock_to_right 16；新建 px-8 py-8 rounded add 16 + label-md + ⌘N mono-sm；检索 px-8 py-6 search 15 + label-sm + ⌘K；模块条目 px-8 py-6 gap-8 图标 16 label-md + 计数 mono-sm；会话组标题 label-sm px-8 pb-4，条目 px-8 py-6，激活圆点 6×6、未激活标题 pl-3.5、时间 mono-sm；底部 p-16 border-t：头像 28×28 → 姓名 label-md+角色 label-sm → 主题按钮 16。
- **导航 60**：py-16 items-center；品牌盒 32×32 SVG 15；新建 36×36 surface 描边 add 18 主色；检索 36×36 无框 search 18；分隔 w-24 border-t my-4；模块 36×36 图标 18 gap-4；底部主题 36×36 图标 17 + 头像 28。
- **导航 224**：与 240 同构；品牌无副标题、新建无 ⌘N、模块无计数、会话无时间戳、底部单行 label-sm「姓名 · 角色」+主题按钮。
- **顶栏**：主态 px-32 py-16 flex-wrap + 元信息行（范围 label-sm · 时间 mono-sm · 来源数 mono-sm），右侧专注阅读（surface 描边）+上下文面板（container-high 无描边、图标主色），按钮 px-8 py-6 rounded-sm 图标 15 + label-sm；专注态 sticky top-0 z-10 + primary-container 徽章（px-8 py-2）+「展开来源(3)」；展开态 px-24 + mono-sm 对照行 + 「检查器已展开」徽章（px-8 py-4）。元信息行**只展示真实可得数据，缺失字段直接省略**，不虚构检索范围、时间或来源数量（C5）。
- **主画布**：提问卡 p-16 rounded-md container 描边，正文 body-md（设计稿含右侧时间 mono-sm；按 C1 决议不显示时间）；检索卡 rounded surface 描边 px-16 py-8，summary=8×8 主色圆点+label-md+mono-sm 统计+expand_more 16，明细 mt-8 pt-8 border-t grid sm:grid-cols-2 gap-8，行=check_circle 14+label-sm+mono-sm 耗时（耗时数据缺失，省略显示）；报告 article gap-24。
- **专注画布**：问题上下文行 pb-16 border-b（body-sm variant + mono-sm）；执行摘要 pl-24 border-l-2 gap-8；footer pt-16 border-t flex-wrap（参考来源 + 链接）。
- **展开画布**：核心结论 pl-16；无提问卡/检索卡/追问 chips。
- **输入区**：主态外层 border-t px-32 py-16，卡片 rounded-md surface 描边 p-16 gap-8：顶行附件芯片（px-8 py-2 rounded-sm container 描边，临时强调+文件名+close 13）与范围按钮（tune 14+label-sm），附件/@/范围为未实现业务，按克制 Soon 占位；textarea rows=2 body-md 无边框；底行 pt-4 border-t：左 attach_file/alternate_email 16+label-sm gap-16，发送 px-16 py-6 主色实心 label-md+arrow_upward 15。专注/展开态：单行卡片 px-16 py-8 flex-row，input body-sm，发送 label-md 无图标。
- **检查器 320**：页签 grid-cols-4 border-b px-8，tab py-12 text-center border-b-2 label-md 无图标；面板 p-16 gap-16；来源项 pb-16 border-b（标题 label-md+mono-sm 相关度，元行 label-sm+mono-sm，摘录 body-sm；相关度数据缺失时省略）；记忆项 mono-sm 日期+body-sm；工具行 py-4 左 mono-sm 工具名右 mono-sm 主色「已完成 · 耗时」（耗时数据缺失，省略）；文档行 py-6 border-b label-md 文件名+mono-sm「范围 · Ready」。
- **检查器 440**：头部 px-16 py-8 border-b，页签 flex gap-16 tab py-4，首项「来源详情 (3)」，仅 close（p-4 图标 16）；预览区 p-16 border-b surface 底：title-md+primary-container 徽章+mono-sm 元行（页码/chunk/相关度）+打开原文按钮（px-8 py-4 container 描边 label-sm）；页码/chunk/相关度数据缺失时按 C2 不渲染或省略，不伪造；段落卡 p-16 rounded container-low 描边：label-sm+mono-sm 头、body-sm+mark、翻页行 pt-4 border-t；列表区 p-16 gap-8：项 p-8 rounded，选中 surface+主色描边，未选中透明描边 hover:container-high。

## 12. 报告排版（含引用胶囊）

设计稿报告是语义化编辑排版，非通用 Markdown 默认样式：
- 核心结论/执行摘要 = border-l-2 primary 引导段（pl-16，专注态 pl-24），标签 label-sm 强调色，正文 body-md；非 Markdown 原生元素。
- **识别规则（实施前先核查）**：先核查现有模型输出是否存在稳定、明确的结构标记。**核心结论标记存在才应用核心结论竖线样式；执行摘要标记存在才应用执行摘要样式；没有标记时按普通正文处理**；不得根据首段位置、段落长度或文本内容猜测。不得修改模型输出协议来迁就 UI，不得破坏 react-markdown 与 remark 插件渲染链。
- h2 = headline-md；章节内 gap-16，报告块间 gap-24；正文 body-md 15/27，strong=font-semibold。
- 表格 = rounded(8) outline-variant 描边 surface 底容器 overflow-x-auto；thead container-low 底 border-b，th px-16 py-8 label-sm variant；td px-16 py-10，行 border-b（末行无）；主数值 mono-sm 强调色。
- 引用胶囊（内联）：px-6 py-2 mx-2 rounded-sm gap-4 items-baseline，container 底描边；范围词 label-sm 强调色 + 文件名 label-sm + 页码 mono-sm；激活态见 §8。**后端目前不产出引用数据，禁止假数据**；无数据时保留内联位置语义，采用克制 Soon 或暂不渲染（占位明显破坏版式时不渲染），不得伪造文件名/页码。
- 延伸追问：flex-wrap gap-8 pt-4；标签 label-sm outline；chip px-8 py-4 rounded-sm surface 描边 label-sm。**无后端数据源**；按 C2 处理：克制 Soon 或暂不渲染。
- 报告结构以设计稿出现的元素为上限，**不新增设计稿外的卡片**来填满页面。
- 缺失数据（引用胶囊/来源列表/来源预览/页码/chunk/相关度/耗时/追问）逐项独立处理：各自保留原位结构，克制 Soon 或暂不渲染，**不得合并成一个大型 Soon 区块**；440px 来源预览无真实来源数据时不得生成虚构的来源详情。
- markdown.css 仅调整 Chat 报告区域所需样式，使用 **Chat 专属作用域**（报告容器类包裹），不得影响其他页面的 Markdown 与排版。

**未定义项汇总**：disabled 视觉、滚动条样式（按 C7 保留现有实现）、窄屏 sticky 行为（C8：不 sticky）、移动端细节、加载骨架屏、toast 样式——设计稿均未定义，实施时沿用现有业务实现或印证已确认决议。