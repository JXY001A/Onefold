import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import LoginForm from "../components/auth/LoginForm";
import RegisterForm from "../components/auth/RegisterForm";
import ResetForm from "../components/auth/ResetForm";
import { useAuth } from "../context/AuthContext";
import type { Me } from "../lib/auth";

type Mode = "login" | "register" | "reset";

const TABS: { key: Mode; label: string }[] = [
  { key: "login", label: "登录" },
  { key: "register", label: "注册" },
  { key: "reset", label: "忘记密码" },
];

/** 身份页：登录 / 注册 / 找回密码三态，成功后跳回来源页。 */
export default function Login() {
  const [mode, setMode] = useState<Mode>("login");
  const [notice, setNotice] = useState<string | null>(null);
  const [account, setAccount] = useState("");

  const { me, setMe } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/chat";

  const done = (user: Me) => {
    setMe(user);
    navigate(from, { replace: true });
  };

  return (
    <section className="mx-auto max-w-sm space-y-4 py-10">
      <h1 className="text-xl font-semibold">归一 · 账号</h1>
      <p className="text-sm text-slate-600">
        游客有 20 轮免费体验，注册后不限轮次。账号用邮箱，密码至少 8 位。
      </p>

      {me?.kind === "user" && (
        <p className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700">
          已登录为 {me.username ?? me.email}，可直接去{" "}
          <Link className="underline" to="/chat">
            对话
          </Link>
          。
        </p>
      )}

      <div className="flex gap-2 border-b border-slate-200 pb-2 text-sm">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => {
              setMode(t.key);
              setNotice(null);
            }}
            className={`rounded-lg px-3 py-1.5 ${
              mode === t.key ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {notice && <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{notice}</p>}

      {mode === "login" && <LoginForm onDone={done} defaultAccount={account} />}
      {mode === "register" && <RegisterForm onDone={done} />}
      {mode === "reset" && (
        <ResetForm
          onDone={(email) => {
            setAccount(email);
            setMode("login");
            setNotice("密码已重置，请用新密码登录");
          }}
        />
      )}
    </section>
  );
}