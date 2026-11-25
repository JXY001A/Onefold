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
import { ensureSession } from "../lib/session";

export function useMemory() {
  const toast = useToast();
  const [data, setData] = useState<MemoryData | null>(null);
  const [loading, setLoading] = useState(true);

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

  const edit = (item: MemoryItem) => {
    const next = window.prompt("编辑记忆内容（留空取消）", item.text);
    if (next === null || !next.trim()) return;
    void run(() => updateMemoryText(item.id, next.trim()), "已更新这条记忆");
  };

  const remove = (item: MemoryItem) => {
    if (!window.confirm("删除这条记忆？")) return;
    void run(() => deleteMemory(item.id), "已删除这条记忆");
  };

  const clearAll = () => {
    if (!window.confirm("清空全部记忆？该操作不可撤销。")) return;
    void run(() => clearMemory(), "已清空全部记忆");
  };

  return { data, loading, toggle, edit, remove, clearAll };
}