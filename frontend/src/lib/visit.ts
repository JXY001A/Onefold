/** 访问记录上报：进入 / 心跳 / 离开。 */

/** 进入页面时上报客户端信息，返回后端生成的 visit_id（失败返回 null，不阻塞页面）。 */
export async function enterVisit(): Promise<string | null> {
  try {
    const res = await fetch("/api/visits/enter", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: window.location.pathname,
        referrer: document.referrer || null,
        screen: `${window.screen.width}x${window.screen.height}`,
        language: navigator.language,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      }),
    });
    if (!res.ok) return null;
    const data: { visit_id?: string } = await res.json();
    return data.visit_id ?? null;
  } catch {
    return null;
  }
}

/** 心跳：刷新最后活跃时间，失败静默忽略。 */
export function heartbeatVisit(visitId: string): void {
  void fetch(`/api/visits/${visitId}/heartbeat`, {
    method: "POST",
    credentials: "include",
    keepalive: true,
  }).catch(() => {});
}

/** 离开：优先用 sendBeacon —— 页面关闭时普通 fetch 会被浏览器丢弃。 */
export function leaveVisit(visitId: string): void {
  const url = `/api/visits/${visitId}/leave`;
  const body = new Blob(["{}"], { type: "application/json" });
  if (navigator.sendBeacon?.(url, body)) return;
  void fetch(url, {
    method: "POST",
    credentials: "include",
    keepalive: true,
  }).catch(() => {});
}