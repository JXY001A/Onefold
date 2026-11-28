# W1 施工方案：结构化引用（Citation）

> 状态：**方案待批准，未改代码**。目标是在现有 RAG 检索基础上，打通「检索 → 引用编号 → 模型标记 → SSE → 落库 → 历史 → UI」。
> 前置：先提交当前五页 UI 改动；W1 涉及前端保护模块的最小增量（见 §7）。

## 1. 现状与缺口

已有：
- `rag/retrieve.py` 返回 `RetrievedChunk`（chunk_id/document_id/page/heading/scope/score/text）；
- `AgentRuntime.run()` 在开始前调用 `retrieve()` 并把片段拼进 system（`context.build_messages` 的 `rag_chunks`）；
- 前端 `lib/sse.ts` 已解析 `citation` 事件（`ChatEvent` 预留）；
- 消息按 `runs → messages` 落库，历史读取在 `services/message_reader.py`。

缺口：
1. Runtime 转 dict 时丢弃了 `chunk_id/document_id/score`，无法生成稳定引用；
2. 没有引用编号与模型标记协议；
3. 后端不发送 `citation` 事件；前端 `useChatStream` 未消费；
4. `messages` 表无引用字段，刷新后引用丢失；
5. 检查器「来源」页签仍是 Soon 占位。

## 2. 协议设计

- 检索结果按出现顺序编号 `c1..cN`（每轮独立，N ≤ 8）。
- system 追加引用目录（每个编号 + 文件名 + 页码 + 章节），并明确：
  「仅可使用以下编号引用；事实性结论句末加 `[c1]`；不确定不要引用；正文中不得出现编号以外的引用格式。」
- 模型输出保留 `[cN]` 标记；后端只做校验，不改写语义。
- 前端渲染：把 `[cN]` 转为文内上标链接（指向报告末尾来源项）；未识别的 `[cN]` 隐藏。
- 引用事件（SSE，`done` 之前按首次出现顺序发送，去重）：
```json
{"type":"citation","data":{
  "index":1,"chunk_id":"...","document_id":"...",
  "filename":"白皮书.pdf","page":14,"heading_path":"一、召回率",
  "scope":"public","score":0.89,"snippet":"不超过 200 字"
}}
```

## 3. 后端改动

| 文件 | 改动 |
|---|---|
| `models/chat.py` | `Message` 新增 `citations_json: Text NULL`（仅 assistant 最终行有值） |
| `migrations/versions/*` | Alembic：新增列（可空，向后兼容） |
| `agent/runtime.py` | ①保留 chunk 元数据并在 `chunks` 中携带 `ref`；②解析最终回答中的 `[cN]`；③生成 citation 列表并通过 `yield` 发送；④transcript 最终 assistant 增加 `citations` |
| `agent/context.py` | RAG 段落前加 `【c1】` 目录与引用规则；已有“标注文件名/页码”改为“使用编号 + 文末来源” |
| `services/run_store.py` | `save_transcript` 读取 `m["citations"]` 写入 `citations_json` |
| `services/message_reader.py` | assistant 行返回 `citations`（JSON 解析失败则为空数组） |
| `services/history*.py` | 回放给 LLM 时忽略 `citations`（OpenAI 形状不受影响） |
| `config.py` | 新增 `rag_citations_enabled: bool = False`（灰度开关） |

不改：检索算法、RRF/rerank、工具协议、chat 路由骨架、并发与配额。

## 4. 前端改动（含保护模块）

| 文件 | 改动 | 级别 |
|---|---|---|
| `lib/sse.ts` | 无需修改（已产出 `citation`） | P0 不动 |
| `lib/chat.ts` | 新增 `Citation` 类型；`ChatMessage.citations?`；`foldRows` 保留历史 `citations`（纯增量） | P0，需批准 |
| `hooks/useChatStream.ts` | 新增 `citation` 分支：按 `index` 追加到当前 assistant（去重），不改流式/回滚 | P0，需批准 |
| `components/chat/MessageItem.tsx` | 正则替换 `[cN]` 为 `[n](#cite-cN)` 链接；渲染文末「参考来源」列表；无引用时不显示 | P2 |
| `components/chat/SourceInspector.tsx` | 「来源」页签从 Soon 改为真实引用列表（同 dedupe 逻辑） | P2 |
| `markdown.css` | 引用链接样式（`sup` / 小胶囊），作用域 `.chat-report` | P2 |

## 5. 历史与刷新

- 保存：最终 assistant 的 `citations` 随 `citations_json` 落库。
- 读取：`message_reader` 返回 `citations`，前端 `foldRows` 映射到消息。
- 旧消息：无字段 → `undefined`，UI 不显示来源，不报错。
- 压缩/摘要：不进入摘要输入，不消耗上下文。

## 6. 测试与验收

离线：
1. 目录编号与检索结果顺序一致；超出 top_k 不出现；
2. 标记解析：合法/重复/未知编号/嵌套文本；未知标记被忽略；
3. `citations_json` 往返：保存→读取→字段一致；旧数据为空；
4. 无检索结果时不发送 citation、不显示来源；
5. `rag_citations_enabled=false` 时行为与当前完全一致。

真实：
- 上传并索引一份含页码的 PDF；
- 提问后报告出现 `[cN]` 上标，点击跳到文末来源；检查器来源页签一致；
- 刷新页面引用仍存在；
- 抽样 20 条结论，引用可定位到原文段落，覆盖率记录在案。

完成条件：离线测试通过；`tsc/build` 通过；截图（浅/深）与覆盖率记录；不新增依赖。

## 7. 保护模块说明

`lib/chat.ts` 与 `hooks/useChatStream.ts` 此前为零修改保护。本次仅允许：
- 新增类型字段与 `citation` 分支；
- 不改 `patchLast`/`rollback`/配额/Abort 语义；
- 不改变 SSE 解析与事件顺序。
如不同意改动这两个文件，备选方案：引用只在当轮显示、刷新丢失（降级），但会失去「可追溯」价值，不建议。

## 8. 五日执行排期（约 25h）

| 日 | 内容 |
|---|---|
| D1 | 迁移 + Message 字段；runtime 保留元数据 + 引用目录注入；开关 |
| D2 | 标记解析 + citation 事件 + transcript/落库；离线单测 |
| D3 | message_reader 返回引用；历史/旧数据回归；接口测试 |
| D4 | 前端类型/fold/useChatStream；MessageItem 上标与来源列表；检查器来源 |
| D5 | 真实 PDF 验收、抽样覆盖率、双主题截图、记录结论与回滚验证 |

## 9. 风险与回滚

- 模型不守标记协议：先度量合规率；不达标则回退到「仅检索来源列表」，不伪造引用。
- 标记污染正文：前端只渲染有效项，未知标记隐藏；后端保存原文，便于回溯。
- 迁移风险：列可空、开关默认关闭；回滚=关开关（行为复原），再回退迁移。
- 性能：只有最终一次正则与去重，O(n) 可忽略。

## 10. 不在 W1 范围

网页/搜索来源的引用、claim 级核验、原文片段查看器、把 RAG 改为显式工具调用、Trace（W3）、多 Agent。
