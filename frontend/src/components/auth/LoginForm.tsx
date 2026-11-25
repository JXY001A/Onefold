import { useState } from "react";
import type { FormEvent } from "react";
import { login, type Me } from "../../lib/auth";
import { PrimaryButton, TextInput } from "../ui/form";

type Props = {
  onDone: (me: Me) => void;
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
    <form onSubmit={submit} className="space-y-gutter-sm">
      <TextInput value={account} onChange={(e) => setAccount(e.target.value)} placeholder="邮箱" autoComplete="username" />
      <TextInput value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="密码" autoComplete="current-password" />
      {error && <p className="font-body text-body-sm text-light-error dark:text-dark-error">{error}</p>}
      <PrimaryButton type="submit" disabled={busy || !account.trim() || password.length < 8} className="w-full">
        {busy ? "登录中…" : "登录"}
      </PrimaryButton>
    </form>
  );
}