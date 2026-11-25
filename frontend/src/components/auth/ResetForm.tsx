import { useState } from "react";
import type { FormEvent } from "react";
import { resetPassword } from "../../lib/auth";
import { Field, PrimaryButton, TextInput } from "../ui/form";
import { EmptyText } from "../ui/kit";
import CodeField from "./CodeField";

type Props = {
  onDone: (email: string) => void;
};

/** 忘记密码：邮箱验证码 + 新密码。改密后旧登录态一律失效。 */
export default function ResetForm({ onDone }: Props) {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await resetPassword({ email: email.trim(), code, password });
      onDone(email.trim());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-gutter-md">
      <EmptyText>输入注册邮箱，收 6 位验证码；验证通过后直接设置新密码。</EmptyText>
      <CodeField purpose="reset" email={email} onEmail={setEmail} code={code} onCode={setCode} disabled={busy} />
      <Field label="新密码（至少 8 位）">
        <TextInput value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="至少 8 位" autoComplete="new-password" />
      </Field>
      {error && <p className="font-body text-body-sm text-light-error dark:text-dark-error">{error}</p>}
      <PrimaryButton type="submit" disabled={busy || code.length !== 6 || password.length < 8} className="w-full">
        {busy ? "提交中…" : "重置密码"}
      </PrimaryButton>
    </form>
  );
}
