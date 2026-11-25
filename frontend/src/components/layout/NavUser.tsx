import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";
import { logout } from "../../lib/auth";
import { ROLE_LABEL } from "../../lib/roles";
import Icon from "../ui/Icon";

/** 左导航底部：头像 → 姓名/角色 → 主题切换；退出/登录为业务追加入口。 */
export default function NavUser({ compact = false }: { compact?: boolean }) {
  const { me, loading, setMe } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();

  const onLogout = async () => {
    if (!window.confirm("退出登录后将以游客身份继续，确定吗？")) return;
    setMe(await logout());
    window.location.assign("/chat");
  };

  const initial = (me?.username || me?.email || "访").slice(0, 1).toUpperCase();
  const name = me?.username || me?.email || "游客";
  const role = me ? ROLE_LABEL[me.role] : "";

  return (
    <div className="flex items-center gap-gutter-sm border-t border-light-outline-variant p-gutter-md dark:border-dark-outline-variant">
      <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-light-outline-variant bg-light-surface font-label text-label-sm text-light-on-surface dark:border-dark-outline-variant dark:bg-dark-surface-container-high dark:text-dark-on-surface">
        {loading ? "…" : initial}
      </span>

      <div className="min-w-0 flex-1">
        {me &&
          (compact ? (
            <p className="truncate font-label text-label-sm text-light-on-surface dark:text-dark-on-surface">{name} · {role}</p>
          ) : (
            <>
              <p className="truncate font-label text-label-md text-light-on-surface dark:text-dark-on-surface">{name}</p>
              <p className="font-label text-label-sm text-light-outline dark:text-dark-outline">{role}</p>
            </>
          ))}
      </div>

      <button
        type="button"
        onClick={toggle}
        aria-label="切换明暗主题"
        title={theme === "dark" ? "切换到亮色" : "切换到暗色"}
        className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-sm text-light-on-surface-variant transition-colors duration-state-change hover:bg-light-surface-container-high dark:text-dark-on-surface-variant dark:hover:bg-dark-surface-container-high"
      >
        <Icon name={theme === "dark" ? "light_mode" : "dark_mode"} size={16} />
      </button>

      {me?.kind === "user" ? (
        <button type="button" onClick={onLogout} title="退出登录" className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-sm text-light-on-surface-variant hover:bg-light-surface-container-high dark:text-dark-on-surface-variant dark:hover:bg-dark-surface-container-high">
          <Icon name="logout" size={16} />
        </button>
      ) : (
        <NavLink to="/login" title="登录 / 注册" className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-sm text-light-primary hover:bg-light-surface-container-high dark:text-dark-primary dark:hover:bg-dark-surface-container-high">
          <Icon name="login" size={16} />
        </NavLink>
      )}
    </div>
  );
}
