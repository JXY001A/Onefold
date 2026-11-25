import type { Skill } from "../../lib/skills";
import { Badge } from "../ui/kit";

/** 2.0 右检查器：仅真实字段；描述、Schema、授权角色、统计等缺失项不伪造。 */
export default function SkillInspector({ skill }: { skill: Skill | null }) {
  return (
    <div className="flex flex-col gap-gutter-md p-gutter-md">
      <h2 className="font-label text-label-sm text-light-outline dark:text-dark-outline">选中 Skill</h2>

      {!skill ? (
        <p className="font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">选择一个 Skill，查看版本与启停状态。</p>
      ) : (
        <>
          <div className="flex flex-col gap-2">
            <div className="flex items-start justify-between gap-gutter-sm">
              <h3 className="min-w-0 break-all font-mono text-title-md text-light-on-surface dark:text-dark-on-surface">{skill.name}</h3>
              <Badge>{skill.version}</Badge>
            </div>
            <p className={`font-label text-label-sm ${skill.enabled ? "text-light-primary dark:text-dark-primary" : "text-light-on-surface-variant dark:text-dark-on-surface-variant"}`}>
              {skill.enabled ? "已启用：会按 frontmatter 描述注入系统提示" : "已停用：不参与本轮对话"}
            </p>
          </div>

          <section className="flex flex-col gap-2 border-t border-light-outline-variant pt-gutter-md dark:border-dark-outline-variant">
            <h3 className="font-label text-label-sm text-light-outline dark:text-dark-outline">调用说明</h3>
            <p className="font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
              启用的 Skill 按描述注入系统提示，正文由 agent 通过 read_skill 按需读取。
            </p>
          </section>

          <p className="border-t border-light-outline-variant pt-gutter-md font-label text-label-sm text-light-outline dark:border-dark-outline-variant dark:text-dark-outline">
            描述、参数 Schema、授权角色与调用统计随后开放。
          </p>
        </>
      )}
    </div>
  );
}
