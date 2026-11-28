import { Link } from "react-router-dom";
import NeuralCanvas from "./NeuralCanvas";

/** Hero 区块：左文案 + 双 CTA / 右侧三维神经网络宇宙（设计稿第 1 屏，整屏占满）。 */
export default function HeroSection() {
  return (
    <section
      data-landing-section
      className="relative flex min-h-[100dvh] w-full flex-col justify-center overflow-hidden pb-20 pt-12 lg:pb-28 lg:pt-20"
    >
      <div className="mx-auto w-full max-w-[1320px] px-6 lg:px-12">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-12 lg:gap-8">
          {/* 左列（约 45%） */}
          <div className="relative z-20 flex flex-col items-start gap-7 lg:col-span-5">
            <div className="inline-flex items-center gap-2.5 rounded-full border border-cosmic-primary/25 bg-cosmic-card/80 px-3 py-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-cosmic-cyan animate-pulse" />
              <span className="font-mono text-[11px] uppercase tracking-widest text-cosmic-secondary">
                PERSONAL AI EXPERIMENT PLATFORM
              </span>
            </div>

            <h1 className="text-[38px] font-semibold leading-[1.12] tracking-[-0.02em] text-cosmic-text sm:text-[46px] lg:text-[52px]">
              探索
              <span className="bg-gradient-to-r from-cosmic-text via-cosmic-primary to-cosmic-purple bg-clip-text text-transparent">
                智能的边界
              </span>
              ，<br />
              创造<span className="text-cosmic-text">自己的可能</span>。
            </h1>

            <p className="max-w-[500px] text-[16px] leading-[1.7] text-cosmic-secondary lg:text-[17px]">
              Onefold 是一个属于个人的 AI 技术实验空间。探索模型与智能体，连接工具与知识，让研究、实验和创造在同一个空间发生。
            </p>

            <div className="flex w-full flex-col items-stretch gap-4 pt-2 sm:flex-row sm:items-start">
              <div className="flex flex-col items-start gap-2">
                <Link
                  to="/chat"
                  className="btn-cosmic-primary inline-flex h-12 w-full min-w-[184px] items-center justify-center gap-2 rounded-lg px-6 text-[15px] font-medium text-white sm:w-auto"
                >
                  <span>以游客身份开始</span>
                  <span className="material-symbols-outlined text-[18px]" aria-hidden="true">
                    arrow_forward
                  </span>
                </Link>
                <span className="text-[12px] text-cosmic-muted">无需注册，立即开始探索。</span>
              </div>

              <div className="flex flex-col items-start gap-2">
                <Link
                  to="/login"
                  className="btn-cosmic-secondary inline-flex h-12 w-full min-w-[164px] items-center justify-center rounded-lg px-6 text-[15px] font-medium text-cosmic-text sm:w-auto"
                >
                  <span>注册 / 登录</span>
                </Link>
                <span className="max-w-[220px] text-[12px] text-cosmic-muted">
                  保存研究历史，使用个人知识库与更多能力。
                </span>
              </div>
            </div>
          </div>

          {/* 右列（约 55%）：体积光晕 + 画布 */}
          <div className="relative flex items-center justify-center lg:col-span-7">
            <div
              className="landing-pulse-slow pointer-events-none absolute h-[340px] w-[340px] rounded-full bg-gradient-to-tr from-cosmic-electric/20 via-cosmic-purple/15 to-cosmic-cyan/10 blur-[72px] sm:h-[480px] sm:w-[480px]"
              aria-hidden="true"
            />
            <div className="relative flex h-[340px] w-full max-w-[660px] items-center justify-center sm:h-[460px] lg:h-[520px]">
              <NeuralCanvas />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
