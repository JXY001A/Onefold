/** 全局轻提示：成功 3 秒自动消失，错误停留 8 秒且可手动关闭。 */

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import ToastViewport, {
  type ToastItem,
  type ToastKind,
} from "../components/common/ToastViewport";

type ToastApi = { push: (kind: ToastKind, message: string) => void };

const ToastContext = createContext<ToastApi | null>(null);

// 最多同时显示 3 条：连续失败时不至于铺满屏幕
const MAX_VISIBLE = 3;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: number) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const push = useCallback(
    (kind: ToastKind, message: string) => {
      const id = Date.now() + Math.random();
      setItems((prev) => [...prev, { id, kind, message }].slice(-MAX_VISIBLE));
      window.setTimeout(() => dismiss(id), kind === "error" ? 8000 : 3000);
    },
    [dismiss],
  );

  const api = useMemo(() => ({ push }), [push]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <ToastViewport items={items} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast 必须在 ToastProvider 内使用");
  return ctx;
}