# 记忆中心布局规范

> 基准视口 1280（Figma）/1440（max-w），桌面稿；无独立移动设计，仅断点行为可推断。页面固定深色。

## 0. 页面根

- 深色容器：`min-h-screen bg-dark-background text-dark-on-background`，并挂 `.dark` 使共享组件的 dark: 变体生效；不随主题切换（用户已确认）。
- 主容器：`max-w-[1440px] mx-auto px-gutter-lg py-gutter-lg flex flex-col gap-gutter-md`。

## 1. Header（Layer 1，底部 hairline）

- 左：H1「记忆中心」（headline-lg）+ 状态徽章 pill；下一行说明文案（body-sm，on-surface-variant）。
- 右（flex wrap，gap-gutter-sm）：全局开关组（label + 开关，`bg-dark-surface border rounded px-gutter-md py-gutter-sm`）→ 「新增记忆」primary 按钮 → 「更多操作」次级按钮（more_horiz + label）+ 下拉菜单（宽 176，导出记忆 / 分隔线 / 清空全部记忆红色）。
- `lg` 以下纵向堆叠。

## 2. 全局关闭横幅（默认隐藏）

- `bg-dark-surface-container-low border rounded px-gutter-md py-gutter-sm`，左：pause_circle + 说明文字；右：「重新开启」文字链（dark-primary）。全局关闭时显示。

## 3. 统计概览（Layer 2）

- 栅格：`grid-cols-2 lg:grid-cols-4 gap-gutter-md`；卡高约 68（py-gutter-sm）。
- 每卡：左列 label-sm + headline 数字；右 32×32 图标盒。四卡顺序固定：全部记忆 / 已激活 / 已停用 / 累计引用。

## 4. 工作区（Layer 3）

- `grid grid-cols-1 lg:grid-cols-[1.85fr_1fr] gap-gutter-lg items-start`。

### 4.1 左列（列表）

1. 工具栏卡（`bg-dark-surface-container-low border rounded p-gutter-md`，内部 gap-gutter-sm）：
   - 第一行：搜索框（flex-1 min-w-200，左内图标）+ 三个下拉（状态 / 类型 / 排序）。
   - 第二行：分类 pills（全部 + 6 大类 + 「更多」展开按钮；展开显示细分分类，可收起）。
2. 列表头：左「共 N 条记忆」（label-sm mono 数字）；右提示「点击记忆查看详情 · 开关即时生效」（mono-sm，dark-outline）。
3. 列表：`flex flex-col gap-gutter-sm`，`lg:max-h-[640px] lg:overflow-y-auto`（自定义滚动条）；窄屏不限高随页面滚动。
4. 列表卡结构：Row1（分类 pill + 类型 pill + 更新于 mono；右侧 已激活/已停用 + 单条开关）→ Row2 正文 2 行截断 → Row3（被引用 N 次 + 最近引用；右侧 编辑/删除 文本按钮）。

### 4.2 右列（详情，lg 下 sticky top-gutter-lg）

- 空态：居中 psychology 图标 + 「选择一条记忆，查看详细信息」（min-h 360）。
- 有选中：头部（记忆详情 + 编辑/删除小按钮）→ 正文区（记忆内容盒、2 列属性网格：分类/记忆类型/激活状态/被引用次数/创建时间/最后更新时间/最近引用(整行)/记忆来源(整行)）→ 引用记录区（标题 + 共 N 次；条目 = 会话名 + 时间 + 「查看来源对话」；空态「暂无详细引用记录」）→ 底部操作条（删除记忆次级红描边 / 编辑记忆 primary）。

## 5. 弹窗

- 编辑弹窗（新增/编辑共用，max-w 540）：内容 textarea（4 行）、分类下拉（6 大类）、类型分段按钮（笔记/卡片）、是否激活开关行、底部 取消/保存记忆。
- 确认弹窗（max-w 440）：warning 图标 + 标题/说明 + 取消/确认删除（清空全部时按钮文案「清空全部」）。

## 6. 响应式

- <lg：主区域单栏堆叠（工具栏 → 列表 → 详情），sticky 失效；统计 2×2；Header 纵排。
- 搜索框 min-w-200，下拉允许换行。
