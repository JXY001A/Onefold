import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";
import { canUseAdmin } from "../../lib/roles";
import { visibleNav } from "../../lib/nav";
import { useWorkspace } from "../../store/workspace";
import Icon from "../ui/Icon";
import Soon from "../ui/Soon";
import BrandMark from "./BrandMark";

const iconBtn =
  "inline-flex h-9 w-9 items-center justify-center rounded transition-colors duration-state-change";

/** 收起的图标导航栏（60px）：品牌 / 新建 / 检索 / 模块图标 / 主题与身份。 */
export default function NavRail() {
  const { me } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();
  const toggleNav = useWorkspace((s) => s.toggleNav);
  const startNew = useWorkspace((s) => s.startNew);
  const running = useWorkspace((s) => s.running);
  const items = visibleNav(me?.role, canUseAdmin(me?.role));
  const initial = (me?.username || me?.email || "访").slice(0, 1).toUpperCase();

  return (
    <aside className="chat-nav flex w-[60px] shrink-0 flex-col items-center justify-between border-r border-light-outline-variant bg-light-surface-container-low py-gutter-md dark:border-dark-outline-variant dark:bg-dark-surface-container-low">
      <div className="flex flex-col items-center gap-gutter-md">
        <button type="button" onClick={toggleNav} aria-label="展开导航" title="展开导航">
          <BrandMark />
        </button>

        <button
          type="button"
          aria-label="新建研究"
          title="新建研究"
          disabled={running}
          onClick={() => {
            startNew();
            navigate("/chat");
          }}
          className={`${iconBtn} border border-light-outline-variant bg-light-surface text-light-primary hover:bg-light-surface-container-high disabled:opacity-50 dark:border-dark-outline-variant dark:bg-dark-surface dark:text-dark-primary dark:hover:bg-dark-surface-container-high`}
        >
          <Icon name="add" size={18} />
        </button>

        <Soon tip="快速检索随后开放">
          <span className={`${iconBtn} text-light-on-surface-variant dark:text-dark-on-surface-variant`}>
            <Icon name="search" size={18} />
          </span>
        </Soon>

        <div className="my-1 w-6 border-t border-light-outline-variant dark:border-dark-outline-variant" />

        <nav className="flex flex-col items-center gap-gutter-xs">
          {items.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              aria-label={n.label}
              title={n.label}
              className={({ isActive }) =>
                `${iconBtn} ${
                  isActive
                    ? "bg-light-surface-container-high text-light-primary dark:bg-dark-surface-container-high dark:text-dark-primary"
                    : "text-light-on-surface-variant hover:bg-light-surface-container-high dark:text-dark-on-surface-variant dark:hover:bg-dark-surface-container-high"
                }`
              }
            >
              <Icon name={n.icon} size={18} />
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="flex flex-col items-center gap-gutter-sm">
        <button type="button" onClick={toggle} aria-label="切换明暗主题" title="切换明暗主题" className={`${iconBtn} text-light-on-surface-variant hover:bg-light-surface-container-high dark:text-dark-on-surface-variant dark:hover:bg-dark-surface-container-high`}>
          <Icon name={theme === "dark" ? "light_mode" : "dark_mode"} size={17} />
        </button>
        <NavLink to={me?.kind === "user" ? "/chat" : "/login"} title={me?.username || "游客"} className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-light-outline-variant bg-light-surface-container-high font-label text-label-sm text-light-on-surface dark:border-dark-outline-variant dark:bg-dark-surface-container-high dark:text-dark-on-surface">
          {initial}
        </NavLink>
      </div>
    </aside>
  );
}