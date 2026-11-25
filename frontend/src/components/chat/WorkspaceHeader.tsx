import { useWorkspace } from "../../store/workspace";
import Icon from "../ui/Icon";

const btnBase = "inline-flex items-center gap-1.5 rounded-sm px-2 py-1.5 font-label text-label-sm transition-colors duration-state-change";
const btnSurface = `${btnBase} border border-light-outline-variant bg-light-surface text-light-on-surface-variant hover:bg-light-surface-container-high dark:border-dark-outline-variant dark:bg-dark-surface dark:text-dark-on-surface-variant dark:hover:bg-dark-surface-container-high`;
const btnPanel = `${btnBase} bg-light-surface-container-high text-light-on-surface dark:bg-dark-surface-container-high dark:text-dark-on-surface`;

/** 本地时间：YYYY-MM-DD HH:mm（仅用于真实会话时间）。 */
function fullTime(iso?: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

/** 工作区顶栏：主态（元信息/开关）/ 专注态（吸附+徽章）/ 检查器展开态（徽章）。 */
export default function WorkspaceHeader() {
  const activeId = useWorkspace((s) => s.activeId);
  const conversations = useWorkspace((s) => s.conversations);
  const focusMode = useWorkspace((s) => s.focusMode);
  const inspectorOpen = useWorkspace((s) => s.inspectorOpen);
  const inspectorExpanded = useWorkspace((s) => s.inspectorExpanded);
  const setFocusMode = useWorkspace((s) => s.setFocusMode);
  const setInspectorOpen = useWorkspace((s) => s.setInspectorOpen);

  const active = conversations.find((c) => c.id === activeId);
  const title = active?.title ?? "新建研究";
  const expandedView = inspectorOpen && inspectorExpanded && !focusMode;
  const variant = focusMode ? "focus" : expandedView ? "expanded" : "main";

  const toggleInspector = () => {
    if (focusMode) {
      setFocusMode(false);
      setInspectorOpen(true);
    } else {
      setInspectorOpen(!inspectorOpen);
    }
  };

  const frame =
    variant === "main"
      ? "flex-wrap px-gutter-xl py-gutter-md"
      : variant === "focus"
        ? "px-gutter-xl py-gutter-md lg:sticky lg:top-0 lg:z-10"
        : "px-gutter-lg py-gutter-md";

  return (
    <header className={`flex items-center justify-between gap-gutter-md border-b border-light-outline-variant bg-light-background dark:border-dark-outline-variant dark:bg-dark-background ${frame}`}>
      <div className="flex min-w-0 items-center gap-gutter-md">
        <div className="min-w-0">
          <h1 className={`font-headline text-headline-lg text-light-on-surface dark:text-dark-on-surface ${variant === "main" ? "text-balance" : "truncate"}`}>{title}</h1>
          {variant === "main" && active && (
            <p className="mt-0.5 font-mono text-mono-sm tabular-nums text-light-outline dark:text-dark-outline">{fullTime(active.updatedAt)}</p>
          )}
        </div>
        {variant === "focus" && (
          <span className="shrink-0 rounded-sm bg-light-primary-container px-2 py-0.5 font-label text-label-sm text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container">
            专注阅读模式
          </span>
        )}
        {variant === "expanded" && (
          <span className="shrink-0 rounded-sm bg-light-surface-container-high px-2 py-1 font-label text-label-sm text-light-on-surface-variant dark:bg-dark-surface-container-high dark:text-dark-on-surface-variant">
            检查器已展开
          </span>
        )}
      </div>

      {variant !== "expanded" && (
        <div className="flex shrink-0 items-center gap-gutter-sm">
          {variant === "focus" ? (
            <>
              <button type="button" onClick={() => setFocusMode(false)} title="退出专注模式" className="inline-flex items-center px-2 py-1.5 font-label text-label-sm text-light-outline hover:text-light-on-surface dark:text-dark-outline dark:hover:text-dark-on-surface">
                退出专注
              </button>
              <button type="button" className={btnPanel} onClick={toggleInspector} title="来源检查器">
                <Icon name="dock_to_left" size={15} className="text-light-primary dark:text-dark-primary" />
                展开来源
              </button>
            </>
          ) : (
            <>
              <button type="button" className={btnSurface} onClick={() => setFocusMode(true)} title="专注阅读模式">
                <Icon name="menu_book" size={15} />
                专注阅读
              </button>
              <button type="button" className={btnPanel} onClick={toggleInspector} title="来源检查器">
                <Icon name="dock_to_left" size={15} className="text-light-primary dark:text-dark-primary" />
                上下文面板
              </button>
            </>
          )}
        </div>
      )}
    </header>
  );
}
