import { Link } from "react-router-dom";

/** 落地页页脚（设计稿第 5 屏）。 */
export default function LandingFooter() {
  return (
    <footer className="w-full border-t border-white/[0.06] bg-cosmic-bg">
      <div className="mx-auto flex max-w-[1320px] flex-col items-start justify-between gap-6 px-6 py-10 sm:flex-row sm:items-center lg:px-12">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-[15px] font-semibold text-cosmic-text">Onefold · 归一</span>
            <span className="text-[12px] text-cosmic-muted">© 2026</span>
          </div>
          <p className="text-[13px] text-cosmic-muted">个人 AI 技术实验与研究平台。</p>
        </div>

        <div className="flex items-center gap-8">
          <a
            href="#capabilities"
            className="text-[13px] text-cosmic-secondary transition-colors hover:text-cosmic-text"
          >
            探索能力
          </a>
          <a
            href="#workspace"
            className="text-[13px] text-cosmic-secondary transition-colors hover:text-cosmic-text"
          >
            工作空间
          </a>
          <Link
            to="/login"
            className="text-[13px] text-cosmic-secondary transition-colors hover:text-cosmic-text"
          >
            登录
          </Link>
        </div>
      </div>
    </footer>
  );
}
