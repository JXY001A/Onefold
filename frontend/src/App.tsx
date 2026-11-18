import { NavLink, Route, Routes } from "react-router-dom";
import { useVisitTracker } from "./hooks/useVisitTracker";
import Landing from "./pages/Landing";
import Chat from "./pages/Chat";
import Documents from "./pages/Documents";
import Skills from "./pages/Skills";
import Admin from "./pages/Admin";

const links = [
  { to: "/", label: "首页" },
  { to: "/chat", label: "对话" },
  { to: "/documents", label: "文档" },
  { to: "/skills", label: "Skill" },
  { to: "/admin", label: "后台" },
];

export default function App() {
  // 整个应用级别记录一次访问（进入 / 心跳 / 离开），与具体页面无关
  useVisitTracker();

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-3">
          <div className="font-semibold tracking-tight">归一 · Onefold</div>
          <nav className="flex gap-4 text-sm">
            {links.map((l) => (
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
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
    </div>
  );
}
