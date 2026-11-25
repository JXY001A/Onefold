import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import LoginForm from "../components/auth/LoginForm";
import RegisterForm from "../components/auth/RegisterForm";
import ResetForm from "../components/auth/ResetForm";
import { Tabs } from "../components/ui/kit";
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
    <div className="h-full overflow-y-auto">
      <div className="px-gutter-xl py-section">
        <section className="mx-auto flex w-full max-w-[384px] flex-col gap-gutter-md">
        <div>
          <h1 className="font-headline text-headline-md text-light-on-surface dark:text-dark-on-surface">归一 · 账号</h1>
          <p className="mt-1 font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
            游客有 20 轮免费体验，注册后不限轮次。账号用邮箱，密码至少 8 位。
          </p>
        </div>

        {me?.kind === "user" && (
          <p className="rounded bg-light-surface-container px-gutter-sm py-gutter-sm font-body text-body-sm text-light-on-surface dark:bg-dark-surface-container dark:text-dark-on-surface">
            已登录为 {me.username ?? me.email}，可直接去{" "}
            <Link className="text-light-primary underline dark:text-dark-primary" to="/chat">对话</Link>。
          </p>
        )}

        <Tabs
          tabs={TABS}
          active={mode}
          variant="segmented"
          className="self-start"
          onChange={(k) => {
            setMode(k as Mode);
            setNotice(null);
          }}
        />

        {notice && (
          <p className="rounded bg-light-primary-container px-gutter-sm py-gutter-sm font-body text-body-sm text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container">
            {notice}
          </p>
        )}

        <div className="rounded-md border border-light-outline-variant bg-light-surface p-gutter-lg dark:border-dark-outline-variant dark:bg-dark-surface">
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
        </div>
        </section>
      </div>
    </div>
  );
}
