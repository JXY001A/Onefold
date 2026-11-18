import { useEffect, useRef } from "react";
import { ensureSession } from "../lib/session";
import { enterVisit, heartbeatVisit, leaveVisit } from "../lib/visit";

/** 心跳间隔：一分钟一次足够判断「人还在看」，又不会把访问表写成高频表。 */
const HEARTBEAT_MS = 60_000;

/**
 * 记录一次访问：进入时建记录，停留期间定时心跳，离开时补上离开时间。
 *
 * 放在 App 里调用（而不是某个页面），这样无论从哪个路由进来都只记一条访问；
 * 身份优先复用已有登录态，没有则先建访客身份（否则后端 401 拿不到归属）。
 */
export function useVisitTracker() {
  const visitId = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void ensureSession()
      .then(() => enterVisit())
      .then((id) => {
        // StrictMode 下 effect 会跑两遍：只认第一次拿到的 visit_id
        if (!cancelled && id && !visitId.current) visitId.current = id;
      })
      .catch(() => {});

    const timer = window.setInterval(() => {
      if (visitId.current) heartbeatVisit(visitId.current);
    }, HEARTBEAT_MS);

    // pagehide 覆盖关闭标签页、跳转、移动端切后台，比 beforeunload 更可靠
    const onHide = () => {
      if (!visitId.current) return;
      leaveVisit(visitId.current);
      // 置空：从 bfcache 恢复后不会拿旧 id 重复上报离开
      visitId.current = null;
    };
    window.addEventListener("pagehide", onHide);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
      window.removeEventListener("pagehide", onHide);
      onHide();
    };
  }, []);
}