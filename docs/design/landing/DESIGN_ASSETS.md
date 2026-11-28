# 落地页设计资产分析

> 分析模式产物，未修改任何业务源代码。
> 来源：`~/Downloads/onefold_the_neural_universe.html`（625 行可渲染 HTML）+ Figma 剪贴板数据（fileKey `boveF0h1bsNeJwKbNPRzJ`，已解码：214 节点、单帧 1440×3052「Html → Body」）。
> 结论：**两份资料互相印证，仅覆盖一张页面——品牌落地页「The Neural Universe」。**

## 1. 资产清单

| 资产 | 是否获得 | 可读性 | 备注 |
|---|---|---|---|
| 页面设计（Figma） | ✅ | 已解析为节点 JSON | 单页 1440×3052 |
| HTML 源文件 | ✅ | ✅ | 625 行，含 3D canvas 脚本 |
| 样式（Tailwind + 自定义 CSS） | ✅ | ✅ | cosmic 色组 + 6 个效果类 |
| 交互状态 | 部分 | ✅ | hover/active 有；focus 未定义 |
| Light / Dark | ❌ | — | 只有深色稿 |
| 响应式 | 隐含 | ✅ | HTML 内 sm/lg 断点类可推断 |
| 工作台页（OnefoldDark） | ❌ | — | HTML 只有跳转链接 |
| 登录页（LoginDark） | ❌ | — | HTML 只有跳转链接 |

## 2. 内容分类

**A. 设计明确规定**：五个区块的结构与全部文案；cosmic 色板与全部字号；卡片/按钮渐变与阴影；悬停位移与描边变化；3D canvas 节点数量、配色、视差参数；Bento 栅格比例（7/5/12）；全部图标（Material Symbols 名称）。

**B. 展示但未说明行为**：CTA 指向的 `../onefold-2-dark/OnefoldDark.html`、`../onefold-v2-login-dark/LoginDark.html` 为 Stitch 占位页，需映射到真实路由；工作区区块的工作台截图（Google 临时外链图片，内容是「理想工作台」而非当前实现）。

**C. 设计未定义**：focus-visible 样式；`prefers-reduced-motion` 下的 canvas 行为；移动端 canvas 降级策略；页面 `<title>`/SEO（沿用现有）。

**D. 无法确定**：工作台、登录页的设计（未提供），本次不实现。

## 3. 已知设计稿内部细节

- `.reveal-section` 类已定义但 HTML 中无 JS 驱动，**无滚动入场动效**，不实现。
- `data-stitch-vh` 为 Stitch 导出标记，无运行时意义。
- 字体加载包含 Inter/Noto 700 字重，但页面实际只用到 600，项目现有字体链接已覆盖，无需追加。
