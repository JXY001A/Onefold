import clsx from "clsx";
import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  /** 悬停提示文案，默认「随后开放」 */
  tip?: string;
  className?: string;
  /** 提示气泡位置，默认上方 */
  place?: "top" | "bottom";
};

/**
 * 「随后开放」禁用包装：保留功能可见，但屏蔽点击并在悬停时给出提示。
 * 用于尚无后端支撑的设计稿功能（检索来源、@引用、原文对照等）。
 */
export default function Soon({ children, tip = "随后开放", className, place = "top" }: Props) {
  return (
    <span className={clsx("group/soon relative inline-flex cursor-not-allowed", className)}>
      <span className="pointer-events-none inline-flex opacity-50 saturate-50">{children}</span>
      <span
        role="tooltip"
        className={clsx(
          "pointer-events-none absolute left-1/2 z-50 -translate-x-1/2 whitespace-nowrap rounded-sm",
          "bg-light-surface-container-highest px-2 py-1 font-label text-label-sm text-light-on-surface",
          "border border-light-outline-variant opacity-0 shadow-lg transition-opacity duration-state-change",
          "group-hover/soon:opacity-100 dark:bg-dark-surface-container-highest dark:text-dark-on-surface dark:border-dark-outline-variant",
          place === "top" ? "bottom-full mb-1.5" : "top-full mt-1.5",
        )}
      >
        {tip}
      </span>
    </span>
  );
}