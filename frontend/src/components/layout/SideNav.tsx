import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { canUseAdmin } from "../../lib/roles";
import { visibleNav } from "../../lib/nav";
import { useWorkspace } from "../../store/workspace";
import Icon from "../ui/Icon";
import Soon from "../ui/Soon";
import BrandMark from "./BrandMark";
import ConversationGroups from "./ConversationGroups";
import NavUser from "./NavUser";
import NavRail from "./NavRail";

/** 视口 <1024：窄屏导航按设计稿整宽展开，忽略初始收起态；>=1024 沿用用户收起状态。 */
function useNarrowViewport() {
  const [narrow, setNarrow] = useState(() => typeof window !== "undefined" && window.innerWidth < 1024);
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1024px)");
    const onChange = () => setNarrow(!mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return narrow;
}

/** 展开式左导航：240px 完整态 / 224px 紧凑态（检查器展开时）。 */
function ExpandedNav({ compact = false }: { compact?: boolean }) {
  const { me } = useAuth();
  const navigate = useNavigate();
  const toggleNav = useWorkspace((s) => s.toggleNav);
  const startNew = useWorkspace((s) => s.startNew);
  const running = useWorkspace((s) => s.running);
  const items = visibleNav(me?.role, canUseAdmin(me?.role));

  const newResearch = () => {
    startNew();
    navigate("/chat");
  };

  return (
    <aside className={`chat-nav flex w-full shrink-0 flex-col border-b border-light-outline-variant bg-light-surface-container-low dark:border-dark-outline-variant dark:bg-dark-surface-container-low lg:border-b-0 lg:border-r ${compact ? "lg:w-[224px]" : "lg:w-[240px]"}`}>
      <div className="flex flex-col gap-gutter-md p-gutter-md">
        {/* 品牌 + 收起 */}
        <div className="flex items-center gap-2">
          <BrandMark sm />
          <div className="min-w-0 flex-1">
            <p className="font-headline text-title-md text-light-on-surface dark:text-dark-on-surface">Onefold</p>
            {!compact && <p className="font-label text-label-sm text-light-outline dark:text-dark-outline">研究工作区</p>}
          </div>
          <button
            type="button"
            onClick={toggleNav}
            aria-label="收起导航"
            title="收起导航"
            className="hidden h-7 w-7 items-center justify-center rounded-sm text-light-outline hover:bg-light-surface-container-high dark:text-dark-outline dark:hover:bg-dark-surface-container-high lg:inline-flex"
          >
            <Icon name="dock_to_right" size={16} />
          </button>
        </div>

        {/* 新建研究 + 快速检索 */}
        <div className="flex flex-col gap-1">
          <button
            type="button"
            onClick={newResearch}
            disabled={running}
            className={`flex w-full items-center rounded border border-light-outline-variant bg-light-surface px-2 py-2 font-label text-label-md text-light-on-surface transition-colors duration-state-change hover:bg-light-surface-container-high disabled:opacity-50 dark:border-dark-outline-variant dark:bg-dark-surface dark:text-dark-on-surface dark:hover:bg-dark-surface-container-high ${
              compact ? "justify-start gap-2" : "justify-between gap-1"
            }`}
          >
            <span className="flex items-center gap-2">
              <Icon name="add" size={16} className="text-light-primary dark:text-dark-primary" />
              新建研究
            </span>
            {!compact && <span className="font-mono text-mono-sm text-light-outline dark:text-dark-outline">⌘N</span>}
          </button>

          <Soon tip="快速检索随后开放" className="w-full">
            <span className="flex w-full items-center gap-2 rounded px-2 py-1.5 font-label text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
              <Icon name="search" size={15} />
              <span className="flex-1 text-left">快速检索</span>
              <span className="font-mono text-mono-sm text-light-outline dark:text-dark-outline">⌘K</span>
            </span>
          </Soon>
        </div>
      </div>

      {/* 模块导航 */}
      <nav className="flex flex-col gap-0.5 border-t border-light-outline-variant px-gutter-md pt-1 dark:border-dark-outline-variant">
        {items.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            className={({ isActive }) =>
              `flex items-center gap-2 rounded px-2 py-1.5 font-label text-label-md transition-colors duration-state-change ${
                isActive
                  ? "bg-light-surface-container-high text-light-on-surface dark:bg-dark-surface-container-high dark:text-dark-on-surface"
                  : "text-light-on-surface-variant hover:bg-light-surface-container-high dark:text-dark-on-surface-variant dark:hover:bg-dark-surface-container-high"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon name={n.icon} size={16} className={isActive ? "text-light-primary dark:text-dark-primary" : ""} />
                {n.label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* 会话分组（桌面内滚；窄屏随整页滚动） */}
      <div className="mt-gutter-md flex min-h-0 flex-col border-t border-light-outline-variant px-gutter-md pt-1 dark:border-dark-outline-variant lg:flex-1">
        <div className="overflow-y-auto pb-gutter-md lg:min-h-0 lg:flex-1">
          <ConversationGroups compact={compact} />
        </div>
      </div>

      <NavUser compact={compact} />
    </aside>
  );
}

/** 左导航入口：专注态固定 60px 图标栏；窄屏整宽展开；桌面按收起状态切换。 */
export default function SideNav() {
  const collapsed = useWorkspace((s) => s.navCollapsed);
  const focusMode = useWorkspace((s) => s.focusMode);
  const inspectorOpen = useWorkspace((s) => s.inspectorOpen);
  const inspectorExpanded = useWorkspace((s) => s.inspectorExpanded);
  const narrow = useNarrowViewport();
  if (focusMode) return <NavRail />;
  if (collapsed && !narrow) return <NavRail />;
  return <ExpandedNav compact={inspectorOpen && inspectorExpanded && !narrow} />;
}
