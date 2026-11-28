import { useEffect } from "react";

/** 整屏翻页导航（用户要求的行为扩展，见 docs/design/landing/LAYOUT_SPEC.md §8）。
 * 桌面滚轮/键盘一次手势 = 缓动过渡一屏（800ms easeInOutCubic）；
 * 触屏与 prefers-reduced-motion 退回原生滚动；
 * 内容高于视口的分屏先以原生滚动阅读，到达边界后再切换相邻屏。 */
export function useLandingPager() {
  useEffect(() => {
    const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!finePointer || reduced) return;

    const topOf = (el: HTMLElement) => el.getBoundingClientRect().top + window.scrollY;
    const sections = () =>
      Array.from(document.querySelectorAll<HTMLElement>("[data-landing-section]"));

    let locked = false;
    let cooldownUntil = 0;
    let acc = 0;
    let accTimer = 0;

    const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

    const animateTo = (target: number) => {
      const start = window.scrollY;
      const dist = target - start;
      if (Math.abs(dist) < 2) return;
      locked = true;
      let t0 = 0;
      const step = (now: number) => {
        if (!t0) t0 = now;
        const t = Math.min(1, (now - t0) / 800);
        window.scrollTo(0, start + dist * ease(t));
        if (t < 1) requestAnimationFrame(step);
        else {
          locked = false;
          cooldownUntil = performance.now() + 250; // 吸收触控板惯性余量
        }
      };
      requestAnimationFrame(step);
    };

    /** 求相邻屏目标；返回 null 表示当前处于超高屏内部，应放行原生滚动。 */
    const neighbor = (dir: 1 | -1): HTMLElement | null => {
      const list = sections();
      if (!list.length) return null;
      const y = window.scrollY;
      const vh = window.innerHeight;
      let idx = 0;
      for (let i = 0; i < list.length; i++) if (topOf(list[i]) <= y + 2) idx = i;
      const cur = list[idx];
      const curTop = topOf(cur);
      const curBottom = curTop + cur.offsetHeight;
      // 40px 容差：仅几十像素的内边距溢出不算"超高"，仍按整屏切换
      if (cur.offsetHeight > vh + 40) {
        const atTop = y <= curTop + 2;
        const atBottom = y + vh >= curBottom - 2;
        if (!(dir === 1 ? atBottom : atTop)) return null;
      }
      return (dir === 1 ? list[idx + 1] : list[idx - 1]) ?? null;
    };

    const onWheel = (e: WheelEvent) => {
      if (locked || performance.now() < cooldownUntil) {
        e.preventDefault();
        return;
      }
      if (e.ctrlKey || Math.abs(e.deltaY) < 2) return;
      const target = neighbor(e.deltaY > 0 ? 1 : -1);
      if (!target) return; // 超高屏内部：整段手势交给原生滚动
      // 边界上从第一个事件就接管，避免原生滚动先漂移导致方向判定失真
      e.preventDefault();
      acc += e.deltaY;
      window.clearTimeout(accTimer);
      accTimer = window.setTimeout(() => (acc = 0), 160);
      if (Math.abs(acc) < 24) return;
      acc = 0;
      animateTo(topOf(target));
    };

    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
      if (e.metaKey || e.ctrlKey || e.altKey || locked) return;
      if (e.key === "PageDown" || e.key === "ArrowDown") {
        const target = neighbor(1);
        if (target) {
          e.preventDefault();
          animateTo(topOf(target));
        }
      } else if (e.key === "PageUp" || e.key === "ArrowUp") {
        const target = neighbor(-1);
        if (target) {
          e.preventDefault();
          animateTo(topOf(target));
        }
      } else if (e.key === "Home" || e.key === "End") {
        const list = sections();
        if (!list.length) return;
        e.preventDefault();
        animateTo(topOf(e.key === "Home" ? list[0] : list[list.length - 1]));
      }
    };

    const onAnchorClick = (e: MouseEvent) => {
      const a = (e.target as HTMLElement | null)?.closest?.('a[href^="#"]');
      if (!a) return;
      const id = a.getAttribute("href")?.slice(1);
      const target = id ? document.getElementById(id) : null;
      if (!target) return;
      e.preventDefault();
      animateTo(topOf(target));
    };

    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("keydown", onKey);
    document.addEventListener("click", onAnchorClick);

    return () => {
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("keydown", onKey);
      document.removeEventListener("click", onAnchorClick);
      window.clearTimeout(accTimer);
    };
  }, []);
}
