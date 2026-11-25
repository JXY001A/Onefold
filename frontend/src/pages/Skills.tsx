import { useCallback, useEffect, useState } from "react";
import { useToast } from "../context/ToastContext";
import { apiRequest } from "../lib/http";
import { ActionLink, EmptyText, PageHeader } from "../components/ui/kit";
import { TableShell, Td, Th, THead } from "../components/ui/table";

type Skill = {
  id: string;
  name: string;
  version: string;
  enabled: boolean;
};

export default function Skills() {
  const toast = useToast();
  const [skills, setSkills] = useState<Skill[]>([]);

  const load = useCallback(async () => {
    try {
      setSkills(await apiRequest<Skill[]>("/api/skills"));
    } catch (exc) {
      toast.push("error", (exc as Error).message);
    }
  }, [toast]);

  useEffect(() => {
    void load();
  }, [load]);

  const toggle = async (skill: Skill) => {
    try {
      await apiRequest(`/api/skills/${skill.id}/enable`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !skill.enabled }),
      });
      toast.push("success", skill.enabled ? `已停用「${skill.name}」` : `已启用「${skill.name}」`);
      await load();
    } catch (exc) {
      toast.push("error", (exc as Error).message);
    }
  };

  return (
    <div className="space-y-gutter-md">
      <PageHeader title="Skill" desc="启用的 Skill 按其 frontmatter 的 description 注入系统提示，正文由 agent 用 read_skill 工具按需读取。" />

      <TableShell>
        <THead>
          <tr>
            <Th>名称</Th>
            <Th>版本</Th>
            <Th>状态</Th>
            <Th className="text-right">操作</Th>
          </tr>
        </THead>
        <tbody>
          {skills.map((s) => (
            <tr key={s.id}>
              <Td>{s.name}</Td>
              <Td className="font-mono text-mono-sm">{s.version}</Td>
              <Td className={s.enabled ? "text-light-primary dark:text-dark-primary" : "text-light-on-surface-variant dark:text-dark-on-surface-variant"}>{s.enabled ? "已启用" : "已停用"}</Td>
              <Td className="text-right"><ActionLink onClick={() => void toggle(s)}>{s.enabled ? "停用" : "启用"}</ActionLink></Td>
            </tr>
          ))}
          {skills.length === 0 && <tr><Td colSpan={4}><EmptyText className="py-gutter-md">还没有 Skill，先往 data/skills 放一个目录。</EmptyText></Td></tr>}
        </tbody>
      </TableShell>
    </div>
  );
}