import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { logout } from "../../lib/auth";
import { canUseAdmin, ROLE_LABEL } from "../../lib/roles";

const LINKS = [
  { to: "/", label: "首页" },
  { to: "/chat", label: "对话" },
  { to: "/documents", label: "文档" },
  { to: "/skills", label: "Skill" },
  { to: "/admin", label: "后台", adminOnly: true },
];

/** 顶栏：导航按角色过滤（后台只对 admin/superadmin 显示），右侧展示身份。 */
export default function TopBar() {
  const { me, loading, setMe } = useAuth();
  const isAdmin = canUseAdmin(me?.role);

  const onLogout = async () => {
    if (!window.confirm("退出登录后将以游客身份继续，确定吗？")) return;
    setMe(await logout());
    // 整页重载：会话列表、配额、访问记录都按新身份重建
    window.location.assign("/chat");
  };

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center gap-4 px-4 py-3">
        <div className="shrink-0 font-semibold tracking-tight">归一 · Onefold</div>

        <nav className="flex flex-1 gap-4 text-sm">
          {LINKS.filter((l) => !l.adminOnly || isAdmin).map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                isActive ? "font-medium text-slate-900" : "text-slate-500 hover:text-slate-900"
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          {loading && <span>…</span>}
          {!loading && me && (
            <>
              <span className="rounded bg-slate-100 px-2 py-0.5 text-slate-700">
                {ROLE_LABEL[me.role]}
              </span>
              {me.username && <span className="max-w-24 truncate" title={me.email ?? undefined}>{me.username}</span>}
              {me.kind === "user" ? (
                <button className="underline hover:text-slate-900" onClick={onLogout}>
                  退出
                </button>
              ) : (
                <NavLink className="text-slate-900 underline" to="/login">
                  登录 / 注册
                </NavLink>
              )}
            </>
          )}
        </div>
      </div>
    </header>
  );
}
