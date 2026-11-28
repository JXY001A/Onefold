# 落地页施工方案（UI Implementation Plan）

> 用户已确认的四项决策：① 范围仅落地页；② `/` 独立整页、脱离 SideNav 外壳（游客开始→`/chat`，登录→`/login`）；③ 新增 `cosmic-*` token + 独立 landing.css，现有 token 不动；④ 固定深色，不跟随主题。
> 未经阶段授权不得修改源代码。

## 1. 修改文件清单

| 文件 | 当前职责 | 修改内容 | 风险 | 涉及业务 | 验收 |
|---|---|---|---|---|---|
| `frontend/src/App.tsx` | 全部路由挂在 SideNav shell 内 | 拆为两个层级：`/` 独立渲染 Landing；其余路由放进 AppShell 嵌套路由（Outlet） | 中（全路由挂载方式变化） | 否 | 6 条路由逐条回归 + 构建 |
| `frontend/tailwind.config.js` | 现有 M3 token | 末尾新增 `colors.cosmic` 一组（纯增量） | 低 | 否 | 构建 + 他页样式抽查 |
| `frontend/src/pages/Landing.tsx` | 旧版首页（43 行） | 重写为区块编排 | 低（P2 纯视觉页） | 否 | 截图对比 |
| `frontend/src/components/landing/landing.css` | 新建 | 效果类，`.landing-root` 作用域 | 低 | 否 | 视觉对比 |
| `frontend/src/components/landing/HeroSection.tsx` | 新建 | Hero 区块 | 低 | 否 | 截图对比 |
| `frontend/src/components/landing/NeuralCanvas.tsx` | 新建 | 3D canvas | 低 | 否 | 动画/性能检查 |
| `frontend/src/components/landing/CapabilitiesSection.tsx` | 新建 | Bento 区块 | 低 | 否 | 截图对比 |
| `frontend/src/components/landing/{Research,Agent,Experiment}Illustration.tsx` | 新建 | 三张内联 SVG | 低 | 否 | 截图对比 |
| `frontend/src/components/landing/WorkspaceSection.tsx` | 新建 | 工作区区块 | 低 | 否 | 截图对比 |
| `frontend/src/components/landing/EntrySection.tsx` | 新建 | 入口区块 | 低 | 否 | 截图对比 |
| `frontend/src/components/landing/LandingFooter.tsx` | 新建 | 页脚 | 低 | 否 | 截图对比 |
| `frontend/public/landing/workspace-preview.png` | 新建 | 从设计稿外链下载的工作台截图 | 低（外链可能失效） | 否 | 图片可渲染 |

**明确不改**：backend、lib/hooks/store/context、其他页面与组件、index.html、既有设计文档。

## 2. 阶段划分

### 阶段 1：底座与路由（基础设施）
- 内容：cosmic 色组、landing.css 骨架（底光/卡片/按钮/呼吸动画）、App.tsx 路由拆分、Landing 空壳（根作用域 + 底光）、下载工作台截图素材。
- 允许修改：上表前 4 项 + 素材文件。
- 禁止修改：其余全部。
- 验收：`npx tsc --noEmit` 与 `npm run build` 通过；`/` 显示全屏深色底光、无侧栏；`/chat`、`/documents`、`/memory`、`/skills`、`/admin`、`/login` 逐条可访问且视觉无变化；1440×1024 截图。
- 回滚：还原 App.tsx 与 tailwind.config.js 两个 diff 即可回到现状。

### 阶段 2：Hero 区块
- 内容：徽标胶囊、H1 渐变字、引导语、双 CTA（含注释行）、NeuralCanvas（含 DPR 限制与视差）。
- 允许修改：HeroSection、NeuralCanvas、Landing.tsx（接入）。
- 验收：1440×1024 截图与设计稿 Hero 区逐项比对（字号、间距、渐变、光晕、canvas 构图）；canvas 持续动画、鼠标视差生效、无 console 错误。
- 回滚：移除 Landing.tsx 中 Hero 引用并删除两个组件文件。

### 阶段 3：能力 Bento 区块
- 内容：区块头 + 7/5/12 栅格 + 三张定制 SVG 插图 + 卡片悬停态。
- 允许修改：CapabilitiesSection、三个 Illustration、Landing.tsx（接入）。
- 验收：三卡比例 704/496/1224、卡高 393/393/226 与设计一致；悬停位移与描边变化符合规范；截图对比。
- 回滚：同上（按文件回退）。

### 阶段 4：工作区 + 入口 + 页脚
- 内容：三步列表、截图卡（本地图片、环境光晕、103% 裁切）、双入口卡、页脚与锚点。
- 允许修改：WorkspaceSection、EntrySection、LandingFooter、Landing.tsx（接入）。
- 验收：截图对比；`#capabilities`/`#workspace` 锚点滚动生效；CTA 跳转 `/chat`、`/login` 正常。
- 回滚：按文件回退。

### 阶段 5：整页回归与响应式
- 内容：390 / 768 / 1024 / 1440 四视口截图比对设计稿；链接与键盘 Tab 走查；构建、类型检查；`git diff` 范围核对。
- 验收：四视口布局与设计稿断点行为一致；无新增 console 错误；diff 仅含清单内文件。
- 回滚：整体 revert 本批文件。

## 3. 视觉验收方法

- 设计侧：用无头 Chrome 渲染设计稿 HTML，截 1440×1024 与 390×844。
- 实现侧：`npm run dev` 后同视口截图（真实应用，非静态预览）。
- 对比项：区块结构 → 尺寸 → 比例 → 位置 → 间距 → 字号 → 颜色 → 边框 → 圆角 → 阴影 → 图标 → 交互态。
- 构建通过不能代替视觉验收；落地页固定深色，不参与双主题比对（用户已确认）。

## 4. 风险与待确认偏差

1. **工作台截图缺失（已按用户决策处理）**：设计稿图片托管于 Google 临时地址，本机网络两次下载均超时。用户确认（2026-11-28）：**先用占位替代，不伪造界面内容**。卡体外壳按设计保留，内部为明确标注「图片素材待补充」的占位；后续拿到原图后仅替换占位内容，不动结构。
2. **保护性偏差（已获批准，2026-11-28）**：
   - a) `prefers-reduced-motion: reduce` 时 canvas 停止动画、渲染静态一帧；
   - b) 页面不可见（切后台）时暂停 canvas 循环。
   - 呼吸光晕与卡片过渡在 reduced-motion 下同样停用（landing.css 已实现）。
3. **字号写法偏差**：设计字号（52/46/38…px）超出项目字号阶梯，采用设计原值任意值写法（`text-[52px]` 等）；颜色一律走 `cosmic-*` token。此偏差仅限落地页目录。
4. **App.tsx 路由拆分**需完整回归 6 条既有路由，防外壳行为回退。

## 5. 施工授权记录（待用户批准后填写）

| 日期 | 批准范围 | 备注 |
|---|---|---|
| 2026-11-28 | 阶段 1（底座与路由） | 每阶段验收后再批准后续阶段；canvas 保护性偏差 a/b 一并批准 |
| 2026-11-28 | 阶段 2（Hero 区块） | 按要求重启了 5173 dev server（旧 tailwind 配置缓存） |
| 2026-11-28 | 阶段 3（能力 Bento 区块） | — |
| 2026-11-28 | 阶段 4（工作区+入口+页脚） | 工作台截图改为占位（用户决策） |
| 2026-11-28 | 阶段 5（整页回归与响应式） | 四视口回归；窄屏高度差已定位为设计稿图片缺失所致 |
| 2026-11-28 | 阶段 6（整屏翻页交互，行为扩展） | 用户追加要求：四屏满视口 + 缓动翻页；页脚并入末屏、超高屏内滚动、触屏保留原生 |
