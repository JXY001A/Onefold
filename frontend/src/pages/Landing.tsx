import "../components/landing/landing.css";
import CapabilitiesSection from "../components/landing/CapabilitiesSection";
import EntrySection from "../components/landing/EntrySection";
import HeroSection from "../components/landing/HeroSection";
import LandingFooter from "../components/landing/LandingFooter";
import WorkspaceSection from "../components/landing/WorkspaceSection";
import { useLandingPager } from "../components/landing/useLandingPager";

/** 品牌落地页（The Neural Universe）：固定深色，独立于应用外壳与主题体系。
 * 四屏整页 + 最后一屏收纳页脚；桌面端整屏翻页导航见 useLandingPager。 */
export default function Landing() {
  useLandingPager();

  return (
    <div className="landing-root relative min-h-screen overflow-x-hidden bg-cosmic-bg text-cosmic-text antialiased selection:bg-cosmic-primary/30 selection:text-cosmic-text">
      {/* 全屏环境底光层 */}
      <div className="landing-ambient pointer-events-none fixed inset-0 z-0" aria-hidden="true" />
      <div className="relative z-10 flex min-h-screen flex-col">
        <main className="w-full flex-1">
          <HeroSection />
          <CapabilitiesSection />
          <WorkspaceSection />
          {/* 最后一屏：入口区 + 页脚贴底 */}
          <div data-landing-section className="flex min-h-[100dvh] flex-col">
            <EntrySection />
            <LandingFooter />
          </div>
        </main>
      </div>
    </div>
  );
}
