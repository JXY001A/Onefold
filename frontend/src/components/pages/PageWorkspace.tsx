import type { ReactNode } from "react";

type Props = {
  /** 页面主内容（默认限宽 820；宽版页面 1100） */
  children: ReactNode;
  /** 右侧详情检查器；无数据时可不传，主内容占满 */
  aside?: ReactNode;
  width?: "default" | "wide";
};

/**
 * 2.0 三栏页面壳：共享左导航（App 层）+ 主内容 820 + 右检查器 320。
 * 名称暂按 2.0 规格实现，窄屏为纵向堆叠，不使用浮层。
 */
export default function PageWorkspace({ children, aside, width = "default" }: Props) {
  const max = width === "wide" ? "max-w-[1100px]" : "max-w-[820px]";
  return (
    <div className="flex min-w-0 flex-col lg:h-full lg:flex-row lg:overflow-hidden">
      <div className="min-w-0 flex-1 lg:overflow-y-auto">
        <div className="px-gutter-xl py-gutter-lg">
          <div className={`mx-auto w-full ${max}`}>{children}</div>
        </div>
      </div>
      {aside && (
        <aside className="w-full shrink-0 border-t border-light-outline-variant bg-light-surface-container-low lg:h-full lg:w-[320px] lg:overflow-y-auto lg:border-l lg:border-t-0 dark:border-dark-outline-variant dark:bg-dark-surface-container-low">
          {aside}
        </aside>
      )}
    </div>
  );
}
