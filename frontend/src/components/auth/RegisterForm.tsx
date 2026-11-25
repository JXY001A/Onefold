import { useState } from "react";
import type { FormEvent } from "react";
import { register, type Me } from "../../lib/auth";
import { PrimaryButton, TextInput } from "../ui/form";
import CodeField from "./CodeField";

type Props = {
  onDone: (me: Me) => void;
};

/** 注册：邮箱验证码 + 密码，昵称可留空（后端取 @ 前部分并去重）。 */
export default function RegisterForm({ onDone }: Props) {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      onDone(await register({ email: email.trim(), code, password, username: username.trim() || undefined }));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-gutter-sm">
      <CodeField purpose="register" email={email} onEmail={setEmail} code={code} onCode={setCode} disabled={busy} />
      <TextInput value={username} onChange={(e) => setUsername(e.target.value)} placeholder="昵称（可选，默认取邮箱前缀）" maxLength={32} />
      <TextInput value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="设置密码（至少 8 位）" autoComplete="new-password" />
      {error && <p className="font-body text-body-sm text-light-error dark:text-dark-error">{error}</p>}
      <PrimaryButton type="submit" disabled={busy || code.length !== 6 || password.length < 8} className="w-full">
        {busy ? "注册中…" : "注册并登录"}
      </PrimaryButton>
    </form>
  );
}