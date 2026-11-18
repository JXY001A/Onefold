let pending: Promise<void> | null = null;

async function bootstrap(): Promise<void> {
  // 已有登录或访客身份就直接用；只有 401 才需要新建访客会话
  const me = await fetch("/api/auth/me", { credentials: "include" });
  if (me.ok) return;
  if (me.status !== 401) throw new Error(`HTTP ${me.status}`);

  const res = await fetch("/api/auth/guest", {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) throw new Error(`创建访客会话失败: HTTP ${res.status}`);
}

export function ensureSession(): Promise<void> {
  // StrictMode 下 effect 会执行两次，复用同一个请求，避免建出两个访客会话
  if (!pending) {
    pending = bootstrap().finally(() => {
      pending = null;
    });
  }
  return pending;
}
