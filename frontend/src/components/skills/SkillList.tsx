import type { Skill } from "../../lib/skills";
import { Badge, EmptyText } from "../ui/kit";

type Props = {
  skills: Skill[];
  selectedId: string | null;
  busyId: string | null;
  onSelect: (id: string) => void;
  onToggle: (skill: Skill) => void;
};

/** 2.0 Skill 列表：仅展示真实字段（名称/版本/启停）；描述、统计等缺失项省略。 */
export default function SkillList({ skills, selectedId, busyId, onSelect, onToggle }: Props) {
  if (skills.length === 0) return <EmptyText className="py-section text-center">还没有 Skill，先往 data/skills 放一个目录。</EmptyText>;

  return (
    <div className="overflow-hidden rounded border border-light-outline-variant bg-light-surface dark:border-dark-outline-variant dark:bg-dark-surface">
      {skills.map((s) => {
        const active = s.id === selectedId;
        return (
          <div
            key={s.id}
            role="button"
            tabIndex={0}
            onClick={() => onSelect(s.id)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelect(s.id);
              }
            }}
            className={`flex cursor-pointer flex-wrap items-center justify-between gap-gutter-md border-b border-light-outline-variant px-gutter-md py-gutter-md last:border-0 dark:border-dark-outline-variant ${
              active ? "bg-light-surface-container dark:bg-dark-surface-container" : "hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container-low"
            }`}
          >
            <div className="flex min-w-0 items-center gap-gutter-sm">
              <span className="truncate font-mono text-body-sm text-light-on-surface dark:text-dark-on-surface">{s.name}</span>
              <Badge>{s.version}</Badge>
            </div>

            <div className="flex shrink-0 items-center gap-gutter-md">
              <span className={`font-label text-label-sm ${s.enabled ? "text-light-primary dark:text-dark-primary" : "text-light-on-surface-variant dark:text-dark-on-surface-variant"}`}>
                {s.enabled ? "已启用" : "已停用"}
              </span>
              <button
                type="button"
                role="switch"
                aria-checked={s.enabled}
                aria-label={`${s.enabled ? "停用" : "启用"} ${s.name}`}
                disabled={busyId === s.id}
                onClick={(e) => {
                  e.stopPropagation();
                  onToggle(s);
                }}
                className={`flex h-5 w-9 shrink-0 items-center rounded-full p-0.5 transition-colors duration-state-change disabled:opacity-40 ${
                  s.enabled ? "bg-light-primary dark:bg-dark-primary" : "bg-light-surface-container-highest dark:bg-dark-surface-container-highest"
                }`}
              >
                <span
                  className={`h-4 w-4 rounded-full bg-light-surface transition-transform duration-state-change dark:bg-dark-surface ${
                    s.enabled ? "translate-x-4" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
