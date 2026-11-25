import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
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
  const { pathname } = useLocation();
  // 仅 Chat 路由在窄屏采用整页纵向滚动；其余路由保持原有固定外壳
  const isChat = pathname === "/chat";

  // 全局初始化一次：确保身份 → 拉会话 → 打开最近一个
  useEffect(() => {
    void init();
  }, [init]);

  return (
    <div className={`${shell} ${isChat ? "flex min-h-screen flex-col lg:h-screen lg:flex-row lg:overflow-hidden" : "flex h-screen overflow-hidden"}`}>
      <SideNav />
      <main className={`flex min-w-0 flex-1 flex-col lg:overflow-hidden ${isChat ? "" : "overflow-hidden"}`}>
        <Routes>
          <Route path="/chat" element={<Chat />} />
          <Route path="/" element={<PageFrame wide><Landing /></PageFrame>} />
          <Route path="/documents" element={<PageFrame wide><Documents /></PageFrame>} />
          <Route path="/memory" element={<PageFrame><Memory /></PageFrame>} />
          <Route path="/skills" element={<PageFrame><Skills /></PageFrame>} />
          <Route path="/admin" element={<PageFrame wide><Admin /></PageFrame>} />
          <Route path="/login" element={<PageFrame><Login /></PageFrame>} />
        </Routes>
      </main>
    </div>
  );
}
