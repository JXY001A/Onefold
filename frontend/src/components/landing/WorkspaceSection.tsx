/** 真实工作区区块：左文案 + 三步列表，右为工作台预览卡。
 * 设计稿此处为工作台截图，其外链素材在本机网络不可达（用户已确认先用占位），
 * 卡体外壳完全按设计保留，内部放明确的待补充占位，不伪造界面内容。 */
export default function WorkspaceSection() {
  const steps = [
    { no: "01", color: "primary", text: "自然语言发起研究。" },
    { no: "02", color: "purple", text: "Agent 搜索与阅读资料。" },
    { no: "03", color: "cyan", text: "整理报告并查看上下文和来源。" },
  ] as const;

  const stepStyle: Record<(typeof steps)[number]["color"], string> = {
    primary: "border-cosmic-primary/30 text-cosmic-primary",
    purple: "border-cosmic-purple/30 text-cosmic-purple",
    cyan: "border-cosmic-cyan/30 text-cosmic-cyan",
  };

  return (
    <section
      data-landing-section
      id="workspace"
      className="relative flex min-h-[100dvh] w-full flex-col justify-center border-t border-white/[0.06] py-20 lg:py-28"
    >
      <div className="mx-auto w-full max-w-[1320px] px-6 lg:px-12">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-12">
          {/* 左列（4 栏） */}
          <div className="flex flex-col gap-6 lg:col-span-4">
            <span className="font-mono text-[11px] uppercase tracking-widest text-cosmic-cyan">
              REAL PRODUCT WORKSPACE
            </span>
            <h2 className="text-[28px] font-semibold leading-[1.2] tracking-tight text-cosmic-text lg:text-[36px]">
              从一个问题，开始一次真正的探索。
            </h2>
            <p className="text-[15px] leading-[1.7] text-cosmic-secondary">
              在同一个工作空间中提问、检索、阅读和整理，让 AI 帮助你推进研究，并保留完整的上下文。
            </p>
            <ul className="flex flex-col gap-4 pt-2">
              {steps.map((s) => (
                <li key={s.no} className="flex items-start gap-3">
                  <span
                    className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md border bg-cosmic-card font-mono text-[11px] ${stepStyle[s.color]}`}
                  >
                    {s.no}
                  </span>
                  <span className="text-[14px] leading-[1.6] text-cosmic-text">{s.text}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* 右列（8 栏）：环境光晕 + 预览卡（占位） */}
          <div className="relative lg:col-span-8">
            <div
              className="pointer-events-none absolute -inset-4 rounded-3xl bg-gradient-to-tr from-cosmic-electric/15 via-cosmic-purple/12 to-cosmic-cyan/10 blur-2xl"
              aria-hidden="true"
            />
            <div className="relative overflow-hidden rounded-2xl border border-cosmic-primary/25 bg-cosmic-card shadow-2xl">
              <div className="flex aspect-[800/344] w-full flex-col items-center justify-center gap-3 bg-cosmic-bg/60">
                <span
                  className="material-symbols-outlined text-[28px] text-cosmic-muted"
                  aria-hidden="true"
                >
                  desktop_windows
                </span>
                <span className="font-mono text-[11px] tracking-wider text-cosmic-muted">
                  工作台预览 · 图片素材待补充
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
