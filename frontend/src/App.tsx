import { Route, Routes } from "react-router-dom";
import TopBar from "./components/layout/TopBar";
import { useVisitTracker } from "./hooks/useVisitTracker";
import Landing from "./pages/Landing";
import Chat from "./pages/Chat";
import Documents from "./pages/Documents";
import Memory from "./pages/Memory";
import Skills from "./pages/Skills";
import Admin from "./pages/Admin";
import Login from "./pages/Login";

export default function App() {
  // 整个应用级别记录一次访问（进入 / 心跳 / 离开），与具体页面无关
  useVisitTracker();

  return (
    <div className="min-h-screen">
      <TopBar />

      <main className="mx-auto max-w-5xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/chat" element={<Chat />} />
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
