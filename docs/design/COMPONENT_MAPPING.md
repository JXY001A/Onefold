# Onefold 2.0 组件映射（COMPONENT_MAPPING）

> 基于真实源码逐一核对（frontend/src/，行数为当前实测）。改造方式四类：保留 / 调整样式 / 拆分 / 新增。
> 实施依据：用户提供的《Onefold 2.0 UI 改版总实施方案（Final Execution Brief）》为最高优先级。
> 设计稿中不存在对应组件的元素标「当前未发现」；数据缺口标【缺】，禁止假数据。
> token 层（tailwind.config.js）与设计稿完全一致，**不改**。未设计页面（文档/记忆/技能/登录/后台）不在本表改造范围。
> 已确认实施决议 C1–C8 见 UI_IMPLEMENTATION_PLAN「已确认实施默认决议」，本表与之一致。

## 1. 组件映射总表

| 现有组件 | 设计稿对应区域 | 当前职责 | 改造方式 | 业务风险 | 验收标准 |
|---|---|---|---|---|---|
| layout/SideNav.tsx (105) | 240px 完整导航 | 品牌行/新建/检索/模块导航/分隔线 | 调整样式；240px 视觉属阶段 1B；224 紧凑态由 inspectorExpanded 派生（C6，属阶段 6，不改 store）；派生前核实 navCollapsed 真实语义，避免覆盖用户主动收起状态 | 新建=startNew、检索=Soon、导航路由与权限过滤（lib/nav）不得变 | 新建为 surface 描边+主色 add+⌘N；条目 px-8 py-6 图标 16；激活仅图标主色；分隔为区块 border-t+pt-4；副标题暂定「研究工作区」（C4，非后端团队名） |
| layout/NavRail.tsx (85) | 60px 图标栏（专注态） | 专注态图标导航 | 保留结构，核对亮暗底色与尺寸；60px 视觉属阶段 7 | 与 SideNav 共享 startNew/路由/Soon | 36px 按钮/18px 图标/17px 主题/28px 头像；分隔 w-24 |
| layout/BrandMark.tsx (18) | 品牌盒 24/32px | 固定 32px+SVG15 | 调整样式：加 size 参数（24+14 / 32+15） | 无逻辑；亮稿底 surface、暗稿 container | 240 态 24px、图标栏 32px，双主题底色正确 |
| layout/ConversationGroups.tsx (71) | 会话分组列表 | 今天/昨天/近7天/更早分组+激活圆点 | 调整样式；分组改 今天/本周/更早（C3：自然周，周一开始） | 会话切换=open(id)，流式中切换行为不得变；formatTime 保留 | 组标题 label-sm px-8 pb-4；条目 gap-0.5；未激活 pl-3.5 variant；亮稿激活项 surface+描边 |
| layout/NavUser.tsx (59) | 底部身份区 | 主题→头像32→姓名→退出 | 调整样式：头像28→姓名/角色→主题；退出为业务追加保留 | 退出登录/主题切换逻辑不得变 | 顺序与尺寸按稿；224 态单行「姓名 · 角色」 |
| chat/WorkspaceHeader.tsx (50) | 中央顶栏三态 | 标题+专注阅读+上下文面板按钮 | 调整样式+拆分（三态变体，≤120 行） | 按钮=toggleFocus/setInspectorOpen；标题来自会话数据；元信息只显示真实可得数据，缺失字段省略，不虚构范围、时间、来源数（C5） | 主态非 sticky+元信息行（C5）；专注 sticky+徽章；展开 px-24+对照行+徽章；窄屏不 sticky（C8）；图标 menu_book |
| chat/MessageList.tsx (68) | 研究画布容器 | 消息列表+空态+自动滚动 | 调整样式：主态 gap-24/py-24，专注 gap-32/py-32 | 自动滚动到底、流式追加渲染不得回归 | 三态限宽 800/820/740 与间距按稿；空态保留（稿未定义） |
| chat/MessageItem.tsx (42) | 提问卡+报告 article | user 卡（surface+「研究问题」标签）/assistant Markdown+标签行 | 调整样式+拆分（ReportBody 子组件） | Markdown 渲染链（react-markdown+插件）不重写；流式 patchLast 只改最后一条；核心结论/执行摘要须按模型输出稳定明确标记识别，无标记不套用竖线样式（不改输出协议、不按首段/段落长度/文本猜测） | 提问卡 container p-16 无标签、不显示时间（C1）；删「归一 · 研究报告」标签行；报告排版见 DESIGN_SYSTEM §12 |
| chat/RetrievalStatus.tsx (36) | 检索状态卡 | details 折叠：圆点+摘要+命中网页列表 | 调整样式 | details 原生折叠、ToolRun 数据流不得变；耗时【缺】不造假 | 圆点 8px；summary on-surface；expand_more 16；明细 grid sm:grid-cols-2；耗时位省略（C2） |
| chat/ChatInput.tsx (77) | 输入区（主态双行卡） | textarea+三 ghost+发送 | 调整样式+新增单行变体；**三态共用同一组件实例与同一输入控件** | 草稿 state 留在 Chat 页；只切 variant，禁止三实例或条件卸载重挂载；发送/停止/quota 逻辑不变 | 顶行附件芯片位+tune 右上（Soon）；底行 pt-4 border-t；body-md rows=2；发送文字后箭头；focus-within 主色描边 |
| chat/SourceInspector.tsx (93) | 320/440 检查器外壳 | 标题行+双按钮+四页签+面板调度 | 调整样式+拆分（InspectorSources/Memory/Docs）；记忆/文档内嵌列表复用现有 API、数据结构、加载状态与错误处理，保留原页面入口与真实空态/错误态；窄屏堆叠（移除 fixed/浮层）属阶段 5 | inspectorTab/inspectorExpanded 读写 store 不得变；不重复造请求层；来源面板保留结构+克制 Soon（C2） | 320 态顶部直接 grid-cols-4 页签（无图标 label-md py-12，激活文字 on-surface）；440 态 flex gap-16+仅 close；窄屏不再浮层；记忆/文档加载、空态与错误提示与现有页面一致 |
| chat/InspectorTools.tsx (47) | 工具面板 mono 行 | 富卡片（链接/标题/简介） | 调整样式：mono 行「工具名 + 已完成」；网页清单保留为二级展开 | ToolRun 数据与 ToolDrawer 入口不得丢；耗时【缺】省略不显示假数值 | py-4 justify-between 左 mono 工具名右 mono 主色状态；展开仍可见真实网页清单 |
| chat/ToolDrawer.tsx (82) | 稿未定义（业务追加） | 全屏抽屉列出搜索/抓取结果 | 保留功能，不改结构；阴影单独评估（稿未定义，不自动全局修改） | Esc 关闭/滚动锁/z-50 层级不得回归 | 功能与交互不变；阴影如需调整须单独确认，且不影响未设计页面 |
| chat/ToolStatus.tsx (39) | 稿无对应行 | 报告标签行内工具状态胶囊 | 调整样式：随标签行移除，状态并入检索卡/工具面板 | 运行中状态提示不得丢失（running 可见） | 主态无「归一 · 研究报告」行；运行状态仍可在检索卡/检查器看到 |
| chat/QuotaBar.tsx (26) | 稿未定义（业务追加） | 游客配额提示+注册引导 | 保留 | isQuotaError 文案耦合（403+「注册」）不得动 | 配额耗尽/未耗尽两态照常显示 |
| ui/Soon.tsx (35) | 稿未定义（用户硬性要求） | 禁点+opacity-50+「随后开放」提示 | 保留禁点与提示；阴影单独评估，不自动全局修改 | 4 处现有 Soon 入口不得变为可点；任何调整不得影响未设计页面 | 悬停提示可见、点击无效；未设计页面视觉不变 |
| ui/Icon.tsx (25) | 全部图标 | 内联 fontSize 渲染 Material Symbols | 保留 | 无 | 各尺寸按 DESIGN_SYSTEM §9；CDN 失败退化已知 |
| ui/kit.tsx (79) | 未设计页面共用 | Card/PageHeader/PillTabs/Badge/EmptyText/ActionLink | 保留（未设计页面不动） | 其他页面视觉不得被波及 | 文档/记忆/技能/后台页视觉与现状一致 |
| layout/PageFrame.tsx (11) | 未设计页面容器 | 独立滚动+限宽 | 保留 | 同上 | 同上 |
| pages/Chat.tsx (92) | 三栏外壳+状态编排 | 组合导航/画布/输入/检查器；窄屏 scrim+fixed 浮层 | 调整样式：删浮层/遮罩，改 lg=1024 纵向堆叠 | 输入 state、useChatStream 回调、会话切换、检查器开合全部不得重建 | <1024 三栏 w-full 堆叠（导航 border-b/检查器 border-t；顺序 导航→画布→检查器，C8）；四态切换不丢输入/消息/流式 |
| App.tsx (41) | 根容器 | h-screen overflow-hidden 固定壳+7 路由 | 调整样式：仅 Chat 路由改外层布局与 min-h 可滚动壳 | 其他六个路由的容器、高度与滚动行为保持不变；无 catch-all 维持现状 | 窄屏整页可滚动；未设计页面仍独立滚动且视觉不变 |
| index.css (121) / markdown.css (97) | 全局基础+报告排版 | 基础样式/自定义滚动条/通用 Markdown 排版 | **不得全量重写**；markdown.css 仅在 **Chat 报告作用域**内按 §12 调整；index.css 仅补 Chat 所需焦点样式 | 使用 Chat 专属作用域隔离，不影响其他页面 Markdown；不动 react-markdown/remark 渲染链；竖线样式仅在识别到明确标记时渲染；滚动条保留（C7） | Chat 报告排版按稿；其他页面 Markdown 视觉不变；Tab 键在 Chat 可见主色 outline；滚动条保留 |
| context/ThemeContext.tsx | 主题预涂+切换 | localStorage+html.dark | 保留 | 预涂脚本（index.html）不得动 | 亮暗切换无闪烁；强调文字成对类生效 |

## 2. 设计元素「当前未发现」清单（需新增或克制 Soon）

| 设计元素 | 现状 | 处置 |
|---|---|---|
| 224px 紧凑导航 | 当前未发现 | 新增：SideNav 派生紧凑态（inspectorExpanded && !focusMode && !navCollapsed），不新增 store 字段（C6）；先核实 navCollapsed 语义，避免覆盖用户主动收起状态 |
| 专注/展开单行输入变体 | 当前未发现 | 新增：ChatInput variant，复用同一实例与同一输入控件，不重挂载 |
| 引用胶囊（内联） | 当前未发现；【缺】后端不发 citation（sse.ts 有类型、useChatStream 未消费） | 保留内联结构语义；克制 Soon，占位明显破坏版式则暂不渲染（C2）；禁止假数据；不与其他缺失项合并成大型 Soon 区块 |
| 延伸追问 chips | 当前未发现；【缺】无建议问题接口 | 同上（C2）；不新增设计稿外卡片 |
| 来源面板/来源预览/段落卡/翻页/mark | 当前未发现真实数据；【缺】无页码/chunk/相关度 | 保留必要布局结构；真实数据存在时才展示，缺失字段不伪造，克制 Soon，破坏设计时暂不渲染（C2）；**不得将整个预览区默认替换为大型 Soon 卡片** |
| 附件芯片/范围按钮/@引用 | 当前未发现；业务未实现 | 按稿位置摆克制 Soon 占位（用户硬性要求） |
| 专注态问题上下文行/执行摘要/footer | 当前未发现 | 新增：问题=首条 user 消息；执行摘要=有明确标记才渲染，否则普通正文；footer 来源数【缺】省略 |
| 核心结论竖线段 | 当前未发现 | 先核查模型输出稳定标记：有则按标记渲染，无则不做竖线段样式；不改输出协议、不改渲染链 |

## 3. 重点保护模块（本轮与实施阶段原则上零修改）

| 模块 | 必须原样保留的行为 |
|---|---|
| lib/http.ts (43) | apiErrorText 双形状错误体解析；STATUS_TEXT 中文兜底；credentials:include |
| lib/sse.ts (174) | parseSSE 事件协议；streamChat 生成器；isQuotaError（403+「注册」文案耦合）；citation 类型预留 |
| lib/chat.ts (121) | foldRows 协议折叠；fetchConversations(days=20)；formatTime；ToolRun/ChatMessage 类型。**C1 已决议：不修改，提问卡不显示时间** |
| store/workspace.ts (113) | initialized 模块级守卫；响应式初始化（<1024 收导航 / ≥1280 开检查器）；全部现有 action。紧凑导航用派生值，不加字段（C6） |
| hooks/useChatStream.ts (117) | patchLast 只改最后一条 assistant；quota 回滚问答对；AbortError 静默；finally setRunning(false)+onRoundDone；meta 回填会话 ID |

## 4. 数据能力矩阵（真实 / 缺失）

| 设计稿数据项 | 能力 | 依据与处置 |
|---|---|---|
| 记忆面板列表 | ✅ 真实 | lib/memory.ts：text/updated_at/category |
| 文档面板「公共 · Ready」 | ✅ 真实 | lib/documents.ts：scope(public/personal/temp)/status/filename |
| 工具名/状态/命中网页 | ✅ 真实 | ToolRun.args/data（web_search/fetch_url） |
| 会话标题/时间/分组 | ✅ 真实 | fetchConversations；会话列表自身时间能力保留，**不得推导为提问卡时间能力**；提问卡不显示时间（C1，不改 lib/chat.ts） |
| 顶栏元信息（范围/来源数） | ❌ 缺失 | C5：只显示真实可得数据，不虚构范围与「N 份参考来源」 |
| 引用胶囊/相关度/页码/chunk | ❌ 缺失 | 后端 agent 未接 RAG；克制 Soon 或暂不渲染（C2） |
| 工具耗时「0.48s」 | ❌ 缺失 | ToolRun 无 duration 字段；省略不显示 |
| 延伸追问/检索范围选择/附件 | ❌ 缺失 | 克制 Soon；不新增设计稿外卡片 |

## 5. 死代码保留（用户明确指令，覆盖审计建议）

TopBar.tsx (69) / ConversationList.tsx (59) / useConversations.ts (85) 当前无调用方，**保留不删**。
react-query / rehype-sanitize / lucide-react 已装未用，本轮不动依赖。

## 6. 工程约束

单文件 ≤200 行、React 组件 ≤120 行（AGENTS.md）：SourceInspector、MessageItem、ChatInput、WorkspaceHeader 增补后必须拆分子文件。
所有样式仅用 token 成对类（禁 slate-*/裸 hex/px-4）；每个 light 类必须有 dark: 对应；中文注释与文案。

## 7. 已记录的设计与业务冲突（不得擅改业务，先记录再确认）

| 冲突 | 设计稿 | 现有业务 | 处置 |
|---|---|---|---|
| 主态顶栏元信息 | 显示检索范围与来源数 | 无范围选择、无来源计数接口 | C5：只显示真实可得数据，不虚构 |
| 窄屏检查器 | 三栏纵向堆叠（lg=1024） | xl 以下 fixed 浮层+遮罩 | 阶段 1A 改堆叠并删浮层，不改业务逻辑 |
| 分组边界 | 今天/本周/更早 | 今天/昨天/近7天/更早 | C3：自然周（周一起）；仅展示分组变化 |
| 检索状态语义 | 「N 个高相关片段」（KB 检索） | 联网工具命中网页 | 沿用现有联网语义，不伪造 KB 检索 |
| 后续新发现 | — | — | 先记录于本表并等待确认，不得擅自改变业务行为 |