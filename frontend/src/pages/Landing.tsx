import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <section className="space-y-6 py-10">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Onefold · Research Agent</p>
      <h1 className="max-w-2xl text-4xl font-semibold leading-tight tracking-tight">
        万般能力，归一入口。
      </h1>
      <p className="max-w-xl text-slate-600">
        一个云端研究助手：联网检索、临时文档问答、Skill 按需加载、MCP 工具调用，回答带引用。
      </p>
      <div className="flex flex-wrap gap-3">
        <Link className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white" to="/chat">
          开始对话
        </Link>
        <Link className="rounded-lg border border-slate-300 px-4 py-2 text-sm" to="/documents">
          上传文档
        </Link>
        <Link className="rounded-lg border border-slate-300 px-4 py-2 text-sm" to="/admin">
          管理后台
        </Link>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">
        <p className="font-medium text-slate-900">骨架状态</p>
        <p className="mt-2">
          当前页面可运行；后端 <code>/healthz</code> 与 <code>/api/chat</code> SSE 已接通。
          业务逻辑（ReAct、RAG、Skill、MCP）按 README 的 TODO 继续实现。
        </p>
      </div>
    </section>
  );
}
