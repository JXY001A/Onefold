/** 文档页的数据与动作：轮询刷新 + 用轻提示反馈，不把原始 HTTP 文本丢到页面上。 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useToast } from "../context/ToastContext";
import {
  collectDoc,
  deleteDoc,
  fetchPersonalDocs,
  fetchPublicDocs,
  publishDoc,
  retryDoc,
  uploadDoc,
  type Doc,
} from "../lib/documents";

export type DocScope = "personal" | "public";

// 文档在后台解析/embedding，轮询让状态自己变化
const POLL_MS = 3000;

export function useDocuments() {
  const toast = useToast();
  const [scope, setScope] = useState<DocScope>("personal");
  const [personal, setPersonal] = useState<Doc[]>([]);
  const [publicDocs, setPublicDocs] = useState<Doc[]>([]);
  // 记住上次弹过的错误：轮询失败时不重复打扰
  const lastError = useRef<string | null>(null);

  const load = useCallback(
    async (silent = false) => {
      try {
        const [mine, shared] = await Promise.all([fetchPersonalDocs(), fetchPublicDocs()]);
        setPersonal(mine);
        setPublicDocs(shared);
        lastError.current = null;
      } catch (exc) {
        const message = (exc as Error).message;
        if (silent || lastError.current === message) return;
        lastError.current = message;
        toast.push("error", message);
      }
    },
    [toast],
  );

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(true), POLL_MS);
    return () => window.clearInterval(timer);
  }, [load]);

  // 统一的「执行动作 → 提示 → 刷新」链路
  const run = useCallback(
    async (action: () => Promise<unknown>, done: string) => {
      try {
        await action();
        toast.push("success", done);
        await load(true);
      } catch (exc) {
        toast.push("error", (exc as Error).message);
      }
    },
    [load, toast],
  );

  const upload = useCallback(
    async (file: File, target: DocScope) => {
      try {
        await uploadDoc(file, target);
        toast.push("success", "已上传，正在解析");
        await load(true);
      } catch (exc) {
        toast.push("error", (exc as Error).message);
      }
    },
    [load, toast],
  );

  return {
    scope,
    setScope,
    docs: scope === "public" ? publicDocs : personal,
    /** 2.0 知识库需要同时展示个人与公共列表（只读派生，不改变原契约） */
    personalDocs: personal,
    publicDocs,
    upload,
    remove: (doc: Doc) => run(() => deleteDoc(doc), "已删除"),
    collect: (id: string) => run(() => collectDoc(id), "已收藏到个人知识库"),
    retry: (doc: Doc) => run(() => retryDoc(doc), "已重新排队解析"),
    publish: (id: string) => run(() => publishDoc(id), "已发布到公共知识库"),
  };
}