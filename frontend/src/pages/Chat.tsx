import { useEffect, useState } from "react";
import { ensureSession } from "../lib/session";
import { streamChat } from "../lib/sse";

type ToolRun = {
  id: string;
  name: string;
  status: "running" | "ok" | "error";
  summary?: string;
};

type Msg = {
  role: "user" | "assistant";
  content: string;
  tools?: ToolRun[];
};

export default function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [ctrl, setCtrl] = useState<AbortController | null>(null);
  const [sessionReady, setSessionReady] = useState(false);

  useEffect(() => {
    // 先确保请求有身份（JWT 或 guest_id），否则聊天接口会返回 401
    let cancelled = false;
    ensureSession()
      .then(() => {
        if (!cancelled) setSessionReady(true);
      })
      .catch((e) => {
        if (!cancelled) setError((e as Error).message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const patchLast = (fn: (m: Msg) => Msg) =>
    setMessages((prev) => {
      const idx = prev.map((m) => m.role).lastIndexOf("assistant");
      if (idx < 0) return prev;
      const next = prev.slice();
      next[idx] = fn(next[idx]);
      return next;
    });

  const send = async () => {
    const text = input.trim();
    if (!text || running || !sessionReady) return;

    setInput("");
    setError(null);
    setStatus("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "", tools: [] },
    ]);

    const controller = new AbortController();
    setCtrl(controller);
    setRunning(true);

    try {
      for await (const ev of streamChat(
        { message: text },
        { signal: controller.signal },
      )) {
        if (ev.type === "queue") {
          setStatus("排队中…");
        } else if (ev.type === "token") {
          setStatus("");
          patchLast((m) => ({ ...m, content: m.content + ev.delta }));
        } else if (ev.type === "tool_call") {
          patchLast((m) => ({
            ...m,
            tools: [
              ...(m.tools ?? []),
              { id: ev.id, name: ev.name, status: "running" },
            ],
          }));
        } else if (ev.type === "tool_result") {
          patchLast((m) => ({
            ...m,
            tools: (m.tools ?? []).map((t) =>
              t.id === ev.id
                ? { ...t, status: ev.ok ? "ok" : "error", summary: ev.summary }
                : t,
            ),
          }));
        } else if (ev.type === "error") {
          setError(ev.message);
          setStatus("");
        }
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        setError((e as Error).message);
      }
    } finally {
      setRunning(false);
      setCtrl(null);
      setStatus("");
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="min-h-[50vh] space-y-4">
        {messages.length === 0 && (
          <p className="py-16 text-center text-sm text-slate-500">
            问一个问题，或上传文档后再问。
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="mb-2 text-xs font-medium text-slate-500">
              {m.role === "user" ? "我" : "归一"}
            </div>
            <p className="whitespace-pre-wrap text-sm leading-6">{m.content}</p>
            {m.tools?.map((t) => (
              <div key={t.id} className="mt-2 rounded-lg border border-slate-200 bg-slate-50 p-2 text-xs">
                <code>{t.name}</code>
                <span className="ml-2 text-slate-500">{t.status}</span>
                {t.summary && <div className="mt-1 text-slate-600">{t.summary}</div>}
              </div>
            ))}
          </div>
        ))}
        {status && <p className="text-center text-sm text-slate-500">{status}</p>}
        {error && <p className="text-center text-sm text-red-600">{error}</p>}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          disabled={running || !sessionReady}
          placeholder={sessionReady ? "输入问题…" : "正在建立访客会话…"}
          className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-500 disabled:bg-slate-50"
        />
        {running ? (
          <button
            onClick={() => ctrl?.abort()}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
          >
            停止
          </button>
        ) : (
          <button
            onClick={send}
            disabled={!sessionReady}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:bg-slate-400"
          >
            发送
          </button>
        )}
      </div>
    </div>
  );
}
