# 设计与业务映射

> 落地页无任何 API 调用，映射重点在「设计元素 → 组件」与「设计链接 → 真实路由」。

## 1. 链接映射

| 设计链接（Stitch 占位） | 实际路由 | 说明 |
|---|---|---|
| `../onefold-2-dark/OnefoldDark.html`（游客开始 ×2） | `/chat` | 现有游客流（guest uuid）已就绪 |
| `../onefold-v2-login-dark/LoginDark.html`（注册/登录 ×3，含页脚） | `/login` | 现有登录页，本次不改视觉 |
| `#capabilities` / `#workspace` | 页内锚点 | 区块 id |

## 2. 设计元素 → 组件映射

| 设计区域 | 设计表现 | 现有对应 | 施工策略 | 分类 |
|---|---|---|---|---|
| 旧 Landing 文案区 | — | `pages/Landing.tsx` 43 行 | 整体替换为设计稿内容 | B |
| Hero 文案/徽标/CTA | 静态 | 无 | 新建 `HeroSection` | C |
| 3D 神经网络 canvas | 动画 + 鼠标视差 | 无 | 新建 `NeuralCanvas`（原生 canvas，无新依赖） | C |
| 能力 Bento 三卡 | 静态 + 3 张内联 SVG | 无 | 新建 `CapabilitiesSection` + 3 个插图组件 | C |
| 工作区截图 | 外链图片 | 无 | 下载本地化到 `public/landing/` | C |
| 入口双卡 | 静态 | 无 | 新建 `EntrySection` | C |
| 页脚 | 静态 | 无 | 新建 `LandingFooter` | C |

> 全部文案以设计稿为准（A 类），不改写、不增删；功能缺口（D 类）为零——本页不依赖任何未实现能力。

## 3. 新组件清单（均遵守 ≤200 行 / 组件 ≤120 行）

| 组件 | 路径 | 职责 |
|---|---|---|
| Landing（页面编排） | `src/pages/Landing.tsx`（重写） | 根作用域、环境底光层、按序组合 5 个区块 |
| HeroSection | `src/components/landing/HeroSection.tsx` | 徽标胶囊、H1 渐变字、引导语、双 CTA |
| NeuralCanvas | `src/components/landing/NeuralCanvas.tsx` | 68 节点斐波那契球分布 + 36 粒子 + 连线 + 鼠标视差 + DPR≤2 |
| CapabilitiesSection | `src/components/landing/CapabilitiesSection.tsx` | 区块头 + 7/5/12 Bento 栅格 |
| ResearchIllustration / AgentIllustration / ExperimentIllustration | `src/components/landing/*.tsx` | 三张内联 SVG，按设计稿原样 |
| WorkspaceSection | `src/components/landing/WorkspaceSection.tsx` | 三步列表 + 截图卡（本地图片） |
| EntrySection | `src/components/landing/EntrySection.tsx` | 双入口卡 |
| LandingFooter | `src/components/landing/LandingFooter.tsx` | 品牌与链接 |
| landing.css | `src/components/landing/landing.css` | 效果类（作用域 `.landing-root` 内） |

## 4. 共享组件影响

- 不复用、不修改 `ui/kit.tsx`、`BrandMark`、`Icon` 等应用组件——落地页视觉体系独立，避免全局污染。
- `PageFrame` 不再包裹 `/`（路由拆分后与 Landing 无关），组件本身零修改。
