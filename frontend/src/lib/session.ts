import { responseErrorText } from "./http";

let pending: Promise<void> | null = null;
let ready = false;

/** 建新访客身份；已存在则顺延 30 天有效期（后端做滑动续期）。 */
async function createOrRenewGuest(): Promise<void> {
  const res = await fetch("/api/auth/guest", {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) throw new Error(`创建访客会话失败：${await responseErrorText(res)}`);
}

async function bootstrap(): Promise<void> {
  // 已有登录或访客身份就直接用；只有 401 才需要新建访客会话
  const me = await fetch("/api/auth/me", { credentials: "include" });
  if (me.ok) {
    const data: { kind?: string } = await me.json().catch(() => ({}));
    // 访客每次进站顺延有效期：否则「近 20 天历史」对访客不成立
    if (data.kind === "guest") await createOrRenewGuest();
    return;
  }
  if (me.status !== 401) throw new Error(await responseErrorText(me));
  await createOrRenewGuest();
}

export function ensureSession(): Promise<void> {
  // 同一次页面生命周期内只需成功一次（App 与页面都会调用）
  if (ready) return Promise.resolve();
  // StrictMode 下 effect 会执行两次，复用同一个请求，避免建出两个访客会话
  if (!pending) {
    pending = bootstrap()
      .then(() => {
        ready = true;
      })
      .finally(() => {
        pending = null;
      });
  }
  return pending;
}