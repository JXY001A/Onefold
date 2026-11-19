import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { fetchMe, type Me } from "../lib/auth";
import { ensureSession } from "../lib/session";

type AuthState = {
  me: Me | null;
  /** 首次身份加载中：此时角色未知，页面别急着判断权限 */
  loading: boolean;
  /** 登录/注册/退出后直接写入，省一次请求 */
  setMe: (me: Me) => void;
  /** 重新拉取（配额变化、角色被改后调用） */
  refresh: () => Promise<void>;
};

const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  // 先确保有身份（登录态或访客），再取角色与配额
  const refresh = useCallback(async () => {
    await ensureSession();
    setMe(await fetchMe());
  }, []);

  useEffect(() => {
    let cancelled = false;
    refresh()
      .catch(() => {
        if (!cancelled) setMe(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  return <Ctx.Provider value={{ me, loading, setMe, refresh }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth 必须在 AuthProvider 内使用");
  return ctx;
}
