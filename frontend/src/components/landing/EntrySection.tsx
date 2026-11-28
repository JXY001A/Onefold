import { Link } from "react-router-dom";

/** 双入口区块：游客体验 / 注册登录（设计稿第 4 屏）。 */
export default function EntrySection() {
  return (
    <section
      id="entry"
      className="relative flex w-full flex-1 flex-col justify-center border-t border-white/[0.06] bg-cosmic-surface/50 py-20 lg:py-28"
    >
      <div className="mx-auto flex w-full max-w-[1120px] flex-col gap-12 px-6 lg:px-12">
        <div className="mx-auto flex max-w-[780px] flex-col gap-3 text-center">
          <h2 className="text-[30px] font-semibold tracking-tight text-cosmic-text lg:text-[40px]">
            你的 AI 探索空间，已经准备就绪。
          </h2>
          <p className="text-[16px] text-cosmic-secondary">从一个问题开始，探索 AI 的更多可能。</p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* 游客体验 */}
          <div className="cosmic-card flex flex-col justify-between gap-8 rounded-2xl p-8">
            <div className="flex flex-col gap-2">
              <span className="font-mono text-[11px] uppercase tracking-wider text-cosmic-cyan">
                GUEST ACCESS
              </span>
              <h3 className="text-[22px] font-semibold text-cosmic-text">游客体验</h3>
              <p className="text-[14px] leading-[1.7] text-cosmic-secondary">
                无需注册即可开始体验 Onefold。
              </p>
            </div>
            <div>
              <Link
                to="/chat"
                className="btn-cosmic-primary inline-flex h-12 w-full min-w-[184px] items-center justify-center gap-2 rounded-lg px-6 text-[15px] font-medium text-white sm:w-auto"
              >
                <span>以游客身份开始</span>
                <span className="material-symbols-outlined text-[18px]" aria-hidden="true">
                  arrow_forward
                </span>
              </Link>
            </div>
          </div>

          {/* 注册 / 登录 */}
          <div className="cosmic-card flex flex-col justify-between gap-8 rounded-2xl p-8">
            <div className="flex flex-col gap-2">
              <span className="font-mono text-[11px] uppercase tracking-wider text-cosmic-purple">
                PERSONAL WORKSPACE
              </span>
              <h3 className="text-[22px] font-semibold text-cosmic-text">注册 / 登录</h3>
              <p className="text-[14px] leading-[1.7] text-cosmic-secondary">
                保存研究历史，使用个人知识库、记忆与 Skill。
              </p>
            </div>
            <div>
              <Link
                to="/login"
                className="btn-cosmic-secondary inline-flex h-12 w-full min-w-[164px] items-center justify-center rounded-lg px-6 text-[15px] font-medium text-cosmic-text sm:w-auto"
              >
                <span>注册 / 登录</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
