import clsx from "clsx";

/** 品牌标识：设计稿折叠六边形。sm=24px（完整导航），默认 32px（图标栏）。 */
export default function BrandMark({ className, sm = false }: { className?: string; sm?: boolean }) {
  const box = sm ? "h-6 w-6" : "h-8 w-8";
  const svg = sm ? 14 : 15;
  return (
    <span
      className={clsx(
        "inline-flex shrink-0 items-center justify-center rounded-sm border",
        "border-light-outline-variant bg-light-surface dark:border-dark-outline-variant dark:bg-dark-surface-container",
        box,
        className,
      )}
    >
      <svg width={svg} height={svg} viewBox="0 0 14 14" fill="none" className="text-light-primary dark:text-dark-primary">
        <path d="M2.5 3.5L7 2L11.5 3.5V10.5L7 12L2.5 10.5V3.5Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
        <path d="M7 2V12" stroke="currentColor" strokeWidth="1.2" />
      </svg>
    </span>
  );
}
