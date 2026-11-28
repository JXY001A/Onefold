/** 记忆中心的确定性 mock 数据：后端暂无引用统计/引用记录/单条停用能力。
 *
 * 约定（见 docs/design/memory-center/COMPONENT_MAPPING.md）：
 * - 同一 id 每次渲染得到相同结果，不写入任何存储，刷新即还原；
 * - UI 上所有来自本模块的字段必须带「示例」微标；
 * - 时间以固定基准（UTC）推算，保证跨环境确定性。
 */

/** 引用记录里展示的示例会话名（设计稿同风格的中文研究对话）。 */
const SESSION_POOL = [
  "多模态检索召回率对比",
  "知识库权限隔离方案",
  "长上下文切片粒度实验",
  "Q3 行业白皮书事实核查",
  "中文词法倒排索引评估",
  "多 Agent 协同延迟评估",
  "白皮书结构大纲梳理",
] as const;

const BASE_TS = Date.UTC(2026, 10, 24, 14, 18); // 固定基准时间，避免测试/渲染漂移

function hashId(id: string): number {
  let h = 7;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return h;
}

function formatTs(daysBack: number, minutesBack: number): string {
  const d = new Date(BASE_TS - daysBack * 86400000 - minutesBack * 60000);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`;
}

/** 被引用次数（0–18）。 */
export function mockCitations(id: string): number {
  return hashId(id) % 19;
}

/** 是否 mock 为「已停用」（约 20%）。 */
export function mockInactive(id: string): boolean {
  return hashId(id) % 5 === 0;
}

/** 最近一次引用时间；0 次引用返回空串。 */
export function mockLastCitedAt(id: string): string {
  const h = hashId(id);
  if (mockCitations(id) === 0) return "";
  return formatTs(h % 12, h % 47);
}

export type CitationLog = { time: string; session: string };

/** 引用记录列表（0–3 条，与引用次数一致：0 次引用时为空）。 */
export function mockCitationLogs(id: string): CitationLog[] {
  const count = mockCitations(id);
  if (count === 0) return [];
  const h = hashId(id);
  const len = 1 + (h % 3);
  return Array.from({ length: len }, (_, i) => ({
    time: formatTs((h + i * 3) % 20, (h + i * 17) % 59),
    session: SESSION_POOL[(h + i) % SESSION_POOL.length],
  }));
}
