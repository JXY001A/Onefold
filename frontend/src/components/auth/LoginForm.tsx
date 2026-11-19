import { useState } from "react";
import type { FormEvent } from "react";
import { login, type Me } from "../../lib/auth";

type Props = {
  onDone: (me: Me) => void;
  /** 重置密码成功后回填邮箱，省一次输入 */
  defaultAccount?: string;
};

/** 登录：account 填邮箱（或旧账号的用户名），密码至少 8 位。 */
export default function LoginForm({ onDone, defaultAccount = "" }: Props) {
  const [account, setAccount] = useState(defaultAccount);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      onDone(await login(account.trim(), password));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <input
        value={account}
        onChange={(e) => setAccount(e.target.value)}
        placeholder="邮箱"
        autoComplete="username"
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
      />
      <input
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        type="password"
        placeholder="密码"
        autoComplete="current-password"
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={busy || !account.trim() || password.length < 8}
        className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:bg-slate-400"
      >
        {busy ? "登录中…" : "登录"}
      </button>
    </form>
  );
}