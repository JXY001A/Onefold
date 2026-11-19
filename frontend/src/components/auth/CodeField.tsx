import { useEffect, useState } from "react";
import { sendCode, type CodePurpose } from "../../lib/auth";

type Props = {
  purpose: CodePurpose;
  email: string;
  onEmail: (value: string) => void;
  code: string;
  onCode: (value: string) => void;
  disabled?: boolean;
};

/** 邮箱 + 验证码：负责发码、60 秒倒计时、dev 模式把码显示出来。 */
export default function CodeField({
  purpose,
  email,
  onEmail,
  code,
  onCode,
  disabled = false,
}: Props) {
  const [sending, setSending] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [hint, setHint] = useState<string | null>(null);
  const [devCode, setDevCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 倒计时：每次 cooldown 变化起一个 1 秒定时器，归零后自动停
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown((n) => n - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  const send = async () => {
    if (sending || cooldown > 0 || !email.trim()) return;
    setSending(true);
    setError(null);
    setDevCode(null);
    try {
      const res = await sendCode(email.trim(), purpose);
      setCooldown(60);
      setHint(`验证码已发送，${Math.round(res.expiresIn / 60)} 分钟内有效`);
      if (res.devCode) setDevCode(res.devCode);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSending(false);
    }
  };

  const inputClass =
    "rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500 disabled:bg-slate-50";

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          value={email}
          onChange={(e) => onEmail(e.target.value)}
          type="email"
          placeholder="邮箱"
          autoComplete="email"
          disabled={disabled}
          className={`flex-1 ${inputClass}`}
        />
        <button
          type="button"
          onClick={send}
          disabled={disabled || sending || cooldown > 0 || !email.trim()}
          className="shrink-0 rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50"
        >
          {cooldown > 0 ? `${cooldown}s 后重发` : sending ? "发送中…" : "获取验证码"}
        </button>
      </div>

      <input
        value={code}
        onChange={(e) => onCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
        inputMode="numeric"
        placeholder="6 位验证码"
        autoComplete="one-time-code"
        disabled={disabled}
        className={`w-full tracking-[0.3em] ${inputClass}`}
      />

      {hint && !error && <p className="text-xs text-slate-500">{hint}</p>}
      {devCode && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
          本地 dev 模式（未配 SMTP），验证码：
          <span className="ml-1 font-mono">{devCode}</span>
        </p>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}