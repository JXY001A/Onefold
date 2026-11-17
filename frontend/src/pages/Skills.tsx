import { useEffect, useState } from "react";

type Skill = {
  id: string;
  name: string;
  version: string;
  enabled: boolean;
};

export default function Skills() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const res = await fetch("/api/skills");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSkills(await res.json());
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const toggle = async (skill: Skill) => {
    await fetch(`/api/skills/${skill.id}/enable`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !skill.enabled }),
    });
    load();
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Skill</h2>
      <p className="text-sm text-slate-500">
        启用的 Skill 按其 frontmatter 的 description 注入系统提示，正文由 agent 用 read_skill
        工具按需读取。
      </p>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        {skills.length === 0 ? (
          <p className="p-6 text-sm text-slate-500">还没有 Skill，先往 data/skills 放一个目录。</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="px-4 py-2">名称</th>
                <th className="px-4 py-2">版本</th>
                <th className="px-4 py-2">状态</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {skills.map((s) => (
                <tr key={s.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">{s.name}</td>
                  <td className="px-4 py-3">{s.version}</td>
                  <td className="px-4 py-3">{s.enabled ? "已启用" : "已停用"}</td>
                  <td className="px-4 py-3 text-right">
                    <button className="text-slate-700 underline" onClick={() => toggle(s)}>
                      {s.enabled ? "停用" : "启用"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
