import type { ReactNode } from "react";

/** 非聊天页的统一容器：独立滚动 + 设计稿留白，居中限宽。 */
export default function PageFrame({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  return (
    <div className="h-full overflow-y-auto">
      <div className={`mx-auto w-full px-gutter-xl py-gutter-lg ${wide ? "max-w-[1100px]" : "max-w-[860px]"}`}>
        {children}
      </div>
    </div>
  );
}