/** 记忆分类：后端 13 类与设计稿 6 大桶的映射，集中管理，禁止散写。 */

/** 后端真实分类（services/memory_categories.py 的词表）。 */
export const MEMORY_CATEGORIES = [
  "身份",
  "职业",
  "教育",
  "技能",
  "项目",
  "目标",
  "偏好",
  "沟通",
  "习惯",
  "关系",
  "约束",
  "兴趣",
  "其他",
] as const;

/** 设计稿 6 大桶；桶内成员按归并映射在文档中登记。 */
export const CATEGORY_BUCKETS: { label: string; members: readonly string[] }[] = [
  { label: "个人信息", members: ["身份"] },
  { label: "职业与技能", members: ["职业", "教育", "技能"] },
  { label: "目标与计划", members: ["目标"] },
  { label: "兴趣与偏好", members: ["偏好", "兴趣"] },
  { label: "项目与工作", members: ["项目"] },
  { label: "其他", members: ["沟通", "习惯", "关系", "约束", "其他"] },
];

/** 「更多」展开的细分分类（真实原分类；"其他"已在主行，不重复）。 */
export const SUBCATEGORY_FILTERS = [
  "身份",
  "职业",
  "教育",
  "技能",
  "项目",
  "目标",
  "偏好",
  "沟通",
  "习惯",
  "关系",
  "约束",
  "兴趣",
] as const;

/** 单条记忆的 category 归入哪个设计桶；未知值归"其他"。 */
export function bucketOf(category: string | null): string {
  const value = category ?? "其他";
  for (const bucket of CATEGORY_BUCKETS) {
    if (bucket.members.includes(value)) return bucket.label;
  }
  return "其他";
}
