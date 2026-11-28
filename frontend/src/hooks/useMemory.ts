/** 记忆页的数据与动作：成功/失败都用轻提示反馈，页面本身只负责渲染。 */

import { useCallback, useEffect, useState } from "react";
import { useToast } from "../context/ToastContext";
import {
  clearMemory,
  deleteMemory,
  fetchMemory,
  setMemoryEnabled,
  updateMemoryText,
  type MemoryData,
  type MemoryItem,
} from "../lib/memory";
import { mockInactive } from "../lib/memoryMock";
import { ensureSession } from "../lib/session";

export function useMemory() {
  const toast = useToast();
  const [data, setData] = useState<MemoryData | null>(null);
  const [loading, setLoading] = useState(true);
  // 单条激活状态是前端 mock（后端无此能力）：只存内存，刷新即还原
  const [activeOverrides, setActiveOverrides] = useState<Record<string, boolean>>({});

  const load = useCallback(async () => {
    try {
      // 访客也要先拿到 guest_id，再访问记忆接口
      await ensureSession();
      setData(await fetchMemory());
    } catch (exc) {
      toast.push("error", (exc as Error).message);
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void load();
  }, [load]);

  // 统一的「执行动作 → 提示 → 刷新」链路
  const run = useCallback(
    async (action: () => Promise<unknown>, done: string) => {
      try {
        await action();
        toast.push("success", done);
        await load();
      } catch (exc) {
        toast.push("error", (exc as Error).message);
      }
    },
    [load, toast],
  );

  const toggle = () => {
    if (!data) return;
    const next = !data.enabled;
    void run(() => setMemoryEnabled(next), next ? "已开启记忆" : "已关闭记忆");
  };

  /** 单条记忆的有效激活状态：mock 默认值之外可被用户临时切换（内存态）。 */
  const isActive = (item: MemoryItem): boolean =>
    activeOverrides[item.id] ?? !mockInactive(item.id);

  const toggleActive = (item: MemoryItem) => {
    const next = !isActive(item);
    setActiveOverrides((prev) => ({ ...prev, [item.id]: next }));
    toast.push("success", next ? "已激活该条记忆（示例操作，刷新还原）" : "已停用该条记忆（示例操作，刷新还原）");
  };

  /** 编辑保存：返回是否成功，供弹窗决定是否关闭。 */
  const saveText = useCallback(
    async (id: string, text: string): Promise<boolean> => {
      try {
        await updateMemoryText(id, text.trim());
        toast.push("success", "已更新这条记忆");
        await load();
        return true;
      } catch (exc) {
        toast.push("error", (exc as Error).message);
        return false;
      }
    },
    [load, toast],
  );

  // 删除/清空的确认弹窗由页面负责，这里只执行动作
  const removeItem = (id: string) => {
    void run(() => deleteMemory(id), "已删除这条记忆");
  };

  const clearAllItems = () => {
    void run(() => clearMemory(), "已清空全部记忆");
  };

  return { data, loading, toggle, saveText, removeItem, clearAllItems, isActive, toggleActive };
}
