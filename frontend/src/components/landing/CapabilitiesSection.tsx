import AgentIllustration from "./AgentIllustration";
import ExperimentIllustration from "./ExperimentIllustration";
import ResearchIllustration from "./ResearchIllustration";

/** 能力区：7/5/12 Bento 栅格三卡（设计稿第 2 屏）。 */
export default function CapabilitiesSection() {
  return (
    <section
      data-landing-section
      id="capabilities"
      className="relative flex min-h-[100dvh] w-full flex-col justify-center border-t border-white/[0.06] bg-cosmic-surface/40 py-8 lg:py-10"
    >
      <div className="mx-auto flex w-full max-w-[1320px] flex-col gap-8 px-6 lg:px-12">
        <div className="flex max-w-[680px] flex-col gap-3">
          <span className="font-mono text-[11px] uppercase tracking-widest text-cosmic-primary">
            EXPLORE AI CAPABILITIES
          </span>
          <h2 className="text-[28px] font-semibold tracking-tight text-cosmic-text lg:text-[38px]">
            一个空间，探索 AI 的更多可能。
          </h2>
          <p className="text-[16px] leading-[1.65] text-cosmic-secondary">
            从研究到智能体，从知识到工具，构建属于自己的 AI 工作方式。
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
          {/* 模块 1：AI Research（7 栏） */}
          <article className="cosmic-card relative flex flex-col gap-4 overflow-hidden rounded-2xl p-6 lg:col-span-7 lg:p-7">
            <div className="relative z-10 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[12px] tracking-wider text-cosmic-cyan">AI Research</span>
                <span className="font-mono text-[11px] text-cosmic-muted">01 · KNOWLEDGE</span>
              </div>
              <h3 className="text-[22px] font-semibold text-cosmic-text">研究与知识探索</h3>
              <p className="max-w-[480px] text-[14px] leading-[1.7] text-cosmic-secondary">
                联网检索、网页阅读、文档分析与知识整理。让复杂问题逐步转化为有结构的研究成果。
              </p>
            </div>
            <div className="flex h-[140px] w-full items-center justify-center overflow-hidden rounded-xl border border-white/[0.05] bg-cosmic-bg/70">
              <ResearchIllustration />
            </div>
          </article>

          {/* 模块 2：AI Agents（5 栏） */}
          <article className="cosmic-card relative flex flex-col gap-4 overflow-hidden rounded-2xl p-6 lg:col-span-5 lg:p-7">
            <div className="relative z-10 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[12px] tracking-wider text-cosmic-purple">AI Agents</span>
                <span className="font-mono text-[11px] text-cosmic-muted">02 · WORKFLOW</span>
              </div>
              <h3 className="text-[22px] font-semibold text-cosmic-text">智能体与工具</h3>
              <p className="text-[14px] leading-[1.7] text-cosmic-secondary">
                探索 Agent、Skill 和工具连接，让 AI 不只是回答问题，还能参与实际工作。
              </p>
            </div>
            <div className="flex h-[140px] w-full items-center justify-center overflow-hidden rounded-xl border border-white/[0.05] bg-cosmic-bg/70">
              <AgentIllustration />
            </div>
          </article>

          {/* 模块 3：AI Experiments（整行 12 栏） */}
          <article className="cosmic-card relative grid grid-cols-1 items-center gap-6 overflow-hidden rounded-2xl p-6 lg:col-span-12 lg:grid-cols-12 lg:p-7">
            <div className="flex flex-col gap-3 lg:col-span-5">
              <div className="flex items-center gap-4">
                <span className="font-mono text-[12px] tracking-wider text-cosmic-primary">AI Experiments</span>
                <span className="font-mono text-[11px] text-cosmic-muted">03 · SANDBOX</span>
              </div>
              <h3 className="text-[22px] font-semibold text-cosmic-text">模型与技术实验</h3>
              <p className="text-[14px] leading-[1.7] text-cosmic-secondary">
                以个人 AI 实验空间为起点，探索不同的 AI 技术、工具与工作方式。
              </p>
            </div>
            <div className="flex h-[120px] w-full items-center justify-center overflow-hidden rounded-xl border border-white/[0.05] bg-cosmic-bg/70 lg:col-span-7">
              <ExperimentIllustration />
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}
