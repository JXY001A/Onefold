import { useWorkspace, type InspectorTab } from "../../store/workspace";
import Icon from "../ui/Icon";
import Soon from "../ui/Soon";
import InspectorDocs from "./InspectorDocs";
import InspectorMemory from "./InspectorMemory";
import InspectorTools from "./InspectorTools";

const TABS: { key: InspectorTab; label: string }[] = [
  { key: "sources", label: "来源" },
  { key: "memory", label: "记忆" },
  { key: "tools", label: "工具" },
  { key: "docs", label: "文档" },
];

/** 右侧检查器：320 页签置顶 / 440 展开（页签 + 仅关闭）；来源能力缺失仅克制提示。 */
export default function SourceInspector() {
  const expanded = useWorkspace((s) => s.inspectorExpanded);
  const tab = useWorkspace((s) => s.inspectorTab);
  const messages = useWorkspace((s) => s.messages);
  const setInspectorOpen = useWorkspace((s) => s.setInspectorOpen);
  const setTab = useWorkspace((s) => s.setInspectorTab);
  const toggleExpanded = useWorkspace((s) => s.toggleExpanded);

  const tools = messages.flatMap((m) => m.tools ?? []);
  const tabBtn = (active: boolean) =>
    `-mb-px border-b-2 font-label text-label-md transition-colors duration-state-change ${
      active
        ? "border-light-primary text-light-on-surface dark:border-dark-primary dark:text-dark-on-surface"
        : "border-transparent text-light-outline hover:text-light-on-surface dark:text-dark-outline dark:hover:text-dark-on-surface"
    }`;

  return (
    <aside className={`flex w-full shrink-0 flex-col border-t border-light-outline-variant bg-light-surface-container-low dark:border-dark-outline-variant dark:bg-dark-surface-container-low lg:h-full lg:border-l lg:border-t-0 ${expanded ? "lg:w-[440px]" : "lg:w-[320px]"}`}>
      {expanded ? (
        <header className="flex items-center justify-between gap-gutter-md border-b border-light-outline-variant px-gutter-md py-2 dark:border-dark-outline-variant">
          <div className="flex items-center gap-gutter-md">
            {TABS.map((t) => (
              <button key={t.key} type="button" onClick={() => setTab(t.key)} className={`${tabBtn(tab === t.key)} py-1`}>
                {t.key === "sources" ? "来源详情" : t.label}
              </button>
            ))}
          </div>
          <button type="button" onClick={() => setInspectorOpen(false)} aria-label="关闭检查器" title="关闭检查器" className="rounded-sm p-1 text-light-outline hover:bg-light-surface-container-high dark:text-dark-outline dark:hover:bg-dark-surface-container-high">
            <Icon name="close" size={16} />
          </button>
        </header>
      ) : (
        <div className="flex items-center border-b border-light-outline-variant pr-1 dark:border-dark-outline-variant">
          <div className="grid flex-1 grid-cols-4 px-2">
            {TABS.map((t) => (
              <button key={t.key} type="button" onClick={() => setTab(t.key)} className={`${tabBtn(tab === t.key)} px-1 py-3 text-center`}>
                {t.label}
              </button>
            ))}
          </div>
          {/* 440 展开入口（设计稿 320 无标题行，保留功能可达） */}
          <button type="button" onClick={toggleExpanded} aria-label="展开检查器" title="展开检查器" className="rounded-sm p-1 text-light-outline hover:bg-light-surface-container-high dark:text-dark-outline dark:hover:bg-dark-surface-container-high">
            <Icon name="open_in_full" size={16} />
          </button>
        </div>
      )}

      <div className="min-h-0 flex-1 overflow-y-auto p-gutter-md">
        {tab === "sources" && (
          <Soon tip="引用来源对照随后开放" className="block">
            <span className="flex items-center gap-2 py-1 font-label text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
              <Icon name="article" size={16} />
              引用来源对照 · 随后开放
            </span>
          </Soon>
        )}
        {tab === "memory" && <InspectorMemory />}
        {tab === "tools" && <InspectorTools tools={tools} />}
        {tab === "docs" && <InspectorDocs />}
      </div>
    </aside>
  );
}
