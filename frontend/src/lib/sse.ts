export type SSEEvent = { event: string; data: string; id?: string };

export async function* parseSSE(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<SSEEvent> {
  const reader = stream.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // 只规范化完整 CRLF；孤立 \r 可能是被切开的 CRLF
      buffer = buffer.replace(/\r\n/g, "\n");

      let idx: number;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const raw = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const evt = parseBlock(raw);
        if (evt) yield evt;
      }
    }
    buffer += decoder.decode();
    buffer = buffer.replace(/\r\n|\r/g, "\n");
    if (buffer.trim()) {
      const evt = parseBlock(buffer);
      if (evt) yield evt;
    }
  } finally {
    reader.releaseLock();
  }
}

function parseBlock(raw: string): SSEEvent | null {
  let event = "message";
  let id: string | undefined;
  const dataLines: string[] = [];

  for (const line of raw.split("\n")) {
    if (!line || line.startsWith(":")) continue;
    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    if (field === "event") event = value;
    else if (field === "data") dataLines.push(value);
    else if (field === "id") id = value;
  }

  if (dataLines.length === 0) return null;
  return { event, data: dataLines.join("\n"), id };
}

export type ChatEvent =
  | { type: "queue"; position: number }
  | { type: "meta"; runId: string; model?: string }
  | { type: "token"; delta: string }
  | { type: "tool_call"; id: string; name: string; arguments: unknown }
  | { type: "tool_result"; id: string; name: string; ok: boolean; summary?: string }
  | { type: "citation"; data: unknown }
  | { type: "done"; usage?: unknown }
  | { type: "error"; code?: string; message: string };

export async function* streamChat(
  body: { message: string; conversation_id?: string; user_id?: string },
  opts: { token?: string; signal?: AbortSignal; url?: string } = {},
): AsyncGenerator<ChatEvent> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`;

  const res = await fetch(opts.url ?? "/api/chat", {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    signal: opts.signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`);
  }
  if (!res.body) throw new Error("响应没有 body");

  for await (const evt of parseSSE(res.body)) {
    let payload: any = {};
    try {
      payload = evt.data ? JSON.parse(evt.data) : {};
    } catch {
      yield { type: "error", message: `非法事件数据: ${evt.event}` };
      continue;
    }

    switch (evt.event) {
      case "queue":
        yield { type: "queue", position: payload.position ?? 0 };
        break;
      case "meta":
        yield { type: "meta", runId: payload.run_id, model: payload.model };
        break;
      case "token":
        yield { type: "token", delta: payload.delta ?? "" };
        break;
      case "tool_call":
        yield { type: "tool_call", id: payload.id, name: payload.name, arguments: payload.arguments };
        break;
      case "tool_result":
        yield {
          type: "tool_result",
          id: payload.id,
          name: payload.name,
          ok: !!payload.ok,
          summary: payload.summary,
        };
        break;
      case "citation":
        yield { type: "citation", data: payload };
        break;
      case "done":
        yield { type: "done", usage: payload.usage };
        break;
      case "error":
        yield { type: "error", code: payload.code, message: payload.message ?? "unknown" };
        break;
      default:
        break;
    }
  }
}
