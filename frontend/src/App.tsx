import { useEffect } from "react";
import { Route, Routes } from "react-router-dom";
import SideNav from "./components/layout/SideNav";
import PageFrame from "./components/layout/PageFrame";
import { useVisitTracker } from "./hooks/useVisitTracker";
import { useWorkspace } from "./store/workspace";
import Landing from "./pages/Landing";
import Chat from "./pages/Chat";
import Documents from "./pages/Documents";
import Memory from "./pages/Memory";
import Skills from "./pages/Skills";
import Admin from "./pages/Admin";
import Login from "./pages/Login";

const shell = "bg-light-background font-body text-light-on-background antialiased dark:bg-dark-background dark:text-dark-on-background";

export default function App() {
  // 应用级访问记录（进入 / 心跳 / 离开）
  useVisitTracker();
  const init = useWorkspace((s) => s.init);

  // 全局初始化一次：确保身份 → 拉会话 → 打开最近一个
  useEffect(() => {
    void init();
  }, [init]);

  return (
    <div className={`${shell} flex min-h-screen flex-col lg:h-screen lg:flex-row lg:overflow-hidden`}>
      <SideNav />
      <main className="flex min-w-0 flex-1 flex-col lg:overflow-hidden">
        <Routes>
          <Route path="/chat" element={<Chat />} />
          <Route path="/" element={<PageFrame wide><Landing /></PageFrame>} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/memory" element={<Memory />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </main>
    </div>
  );
}
