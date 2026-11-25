import { useCallback, useEffect, useState } from "react";
import PageWorkspace from "../components/pages/PageWorkspace";
import SkillInspector from "../components/skills/SkillInspector";
import SkillList from "../components/skills/SkillList";
import Icon from "../components/ui/Icon";
import Soon from "../components/ui/Soon";
import { PageHeader } from "../components/ui/kit";
import { useToast } from "../context/ToastContext";
import { fetchSkills, setSkillEnabled, type Skill } from "../lib/skills";

/** Skill 管理（2.0 视觉壳 + 真实数据）：分类/新建/编辑/统计/Schema 按决议省略。 */
export default function Skills() {
  const toast = useToast();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setSkills(await fetchSkills());
      setError(null);
    } catch (exc) {
      setError((exc as Error).message);
      toast.push("error", (exc as Error).message);
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void load();
  }, [load]);

  const activeId = skills.some((s) => s.id === selectedId) ? selectedId : skills[0]?.id ?? null;
  const selected = skills.find((s) => s.id === activeId) ?? null;

  const toggle = async (skill: Skill) => {
    if (busyId) return;
    setBusyId(skill.id);
    try {
      await setSkillEnabled(skill.id, !skill.enabled);
      toast.push("success", skill.enabled ? `已停用「${skill.name}」` : `已启用「${skill.name}」`);
      await load();
    } catch (exc) {
      toast.push("error", (exc as Error).message);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <PageWorkspace aside={<SkillInspector skill={selected} />}>
      <div className="flex flex-col gap-gutter-lg">
        <PageHeader
          title="Skill 管理"
          desc="管理研究助手与多 Agent 可调用的标准化能力模块、触发规则与权限边界。"
          actions={
            <Soon tip="导入 Skill 随后开放" place="bottom">
              <span className="inline-flex items-center gap-1.5 rounded border border-light-outline-variant px-gutter-md py-2 font-label text-label-md text-light-on-surface dark:border-dark-outline-variant dark:text-dark-on-surface">
                <Icon name="upload_file" size={16} />
                导入 Skill
              </span>
            </Soon>
          }
        />

        {loading && <p className="py-section text-center font-label text-label-sm text-light-outline dark:text-dark-outline">加载中…</p>}
        {!loading && error && <p className="py-section text-center font-label text-label-sm text-light-error dark:text-dark-error">{error}</p>}
        {!loading && !error && (
          <SkillList skills={skills} selectedId={activeId} busyId={busyId} onSelect={setSelectedId} onToggle={(s) => void toggle(s)} />
        )}
      </div>
    </PageWorkspace>
  );
}
