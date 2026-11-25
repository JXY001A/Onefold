import { create } from "zustand";
import type { Dispatch, SetStateAction } from "react";
import { fetchConversations, fetchMessages, type ChatMessage, type Conversation } from "../lib/chat";
import { ensureSession } from "../lib/session";

export type InspectorTab = "sources" | "memory" | "tools" | "docs";

type WorkspaceState = {
  conversations: Conversation[];
  activeId: string | null;
  messages: ChatMessage[];
  ready: boolean;
  loading: boolean;
  error: string | null;
  /** 流式生成中：切换会话/新建在此期间禁用 */
  running: boolean;
  // 外壳与检查器 UI 状态
  navCollapsed: boolean;
  inspectorOpen: boolean;
  inspectorExpanded: boolean;
  focusMode: boolean;
  inspectorTab: InspectorTab;
  // 动作
  init: () => Promise<void>;
  refresh: () => Promise<void>;
  open: (id: string) => Promise<void>;
  startNew: () => void;
  setActiveId: (id: string | null) => void;
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>;
  setError: (e: string | null) => void;
  setRunning: (v: boolean) => void;
  toggleNav: () => void;
  setInspectorOpen: (v: boolean) => void;
  toggleExpanded: () => void;
  setFocusMode: (v: boolean) => void;
  setInspectorTab: (t: InspectorTab) => void;
};

let initialized = false;

/** 首屏按视口宽度决定初始形态：窄屏收导航、关检查器，避免中栏被挤压。 */
const wide = typeof window !== "undefined" ? window.innerWidth : 1440;

/** 全局工作区：左导航与研究工作区共用同一份会话/消息状态。 */
export const useWorkspace = create<WorkspaceState>((set, get) => ({
  conversations: [],
  activeId: null,
  messages: [],
  ready: false,
  loading: false,
  error: null,
  running: false,
  navCollapsed: wide < 1024,
  inspectorOpen: wide >= 1280,
  inspectorExpanded: false,
  focusMode: false,
  inspectorTab: "sources",

  init: async () => {
    if (initialized) return;
    initialized = true;
    try {
      await ensureSession();
      const list = await fetchConversations();
      set({ conversations: list });
      const latest = list[0];
      if (latest) {
        const history = await fetchMessages(latest.id).catch(() => null);
        if (history) set({ activeId: latest.id, messages: history });
      }
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ ready: true });
    }
  },

  refresh: async () => {
    try {
      set({ conversations: await fetchConversations() });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  open: async (id) => {
    if (get().running || id === get().activeId) return;
    set({ loading: true, error: null });
    try {
      const history = await fetchMessages(id);
      set({ activeId: id, messages: history });
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ loading: false });
    }
  },

  startNew: () => {
    if (get().running) return;
    set({ activeId: null, messages: [], error: null, focusMode: false });
  },

  setActiveId: (id) => set({ activeId: id }),
  setMessages: (updater) =>
    set((s) => ({ messages: typeof updater === "function" ? updater(s.messages) : updater })),
  setError: (e) => set({ error: e }),
  setRunning: (v) => set({ running: v }),
  toggleNav: () => set((s) => ({ navCollapsed: !s.navCollapsed })),
  setInspectorOpen: (v) => set({ inspectorOpen: v }),
  toggleExpanded: () => set((s) => ({ inspectorExpanded: !s.inspectorExpanded })),
  setFocusMode: (v) => set({ focusMode: v }),
  setInspectorTab: (t) => set({ inspectorTab: t }),
}));