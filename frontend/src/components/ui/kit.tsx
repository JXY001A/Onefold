import clsx from "clsx";
import type { ReactNode } from "react";

/** 表面卡片：统一圆角与边框，暗亮通用。 */
export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={clsx("rounded-md border border-light-outline-variant bg-light-surface dark:border-dark-outline-variant dark:bg-dark-surface", className)}>
      {children}
    </div>
  );
}

/** 页头：标题 + 描述 + 右侧操作区。 */
export function PageHeader({ title, desc, actions }: { title: string; desc?: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-gutter-md">
      <div>
        <h2 className="font-headline text-headline-md text-light-on-surface dark:text-dark-on-surface">{title}</h2>
        {desc && <p className="mt-1 font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">{desc}</p>}
      </div>
      {actions && <div className="flex items-center gap-gutter-sm">{actions}</div>}
    </div>
  );
}

type Tab = { key: string; label: string };

/** 胶囊标签页：选中态用主色容器，用于知识库 / 后台 / 账号。 */
export function PillTabs({ tabs, active, onChange }: { tabs: Tab[]; active: string; onChange: (key: string) => void }) {
  return (
    <div className="flex flex-wrap gap-gutter-sm">
      {tabs.map((t) => (
        <button
          key={t.key}
          type="button"
          onClick={() => onChange(t.key)}
          className={clsx(
            "rounded-sm px-gutter-md py-1.5 font-label text-label-md transition-colors duration-state-change",
            active === t.key
              ? "bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary"
              : "border border-light-outline-variant text-light-on-surface-variant hover:bg-light-surface-container-high dark:border-dark-outline-variant dark:text-dark-on-surface-variant dark:hover:bg-dark-surface-container-high",
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

/** 小徽章：分类 / 状态标记。 */
export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "primary" | "warning" }) {
  const tones = {
    neutral: "bg-light-surface-container-high text-light-on-surface-variant dark:bg-dark-surface-container-high dark:text-dark-on-surface-variant",
    primary: "bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container",
    warning: "bg-light-warning-container text-light-on-warning-container dark:bg-dark-warning-container dark:text-dark-on-warning-container",
  };
  return <span className={clsx("rounded-sm px-2 py-0.5 font-label text-label-sm", tones[tone])}>{children}</span>;
}

/** 空态 / 次要说明文字。 */
export function EmptyText({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={clsx("font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant", className)}>{children}</p>;
}

/** 文字操作按钮（编辑/删除/重试等），统一 underline 风格。 */
export function ActionLink({ children, onClick, tone = "default", disabled }: { children: ReactNode; onClick?: () => void; tone?: "default" | "primary" | "danger" | "warning"; disabled?: boolean }) {
  const tones = {
    default: "text-light-on-surface-variant dark:text-dark-on-surface-variant",
    primary: "text-light-primary dark:text-dark-primary",
    danger: "text-light-error dark:text-dark-error",
    warning: "text-light-warning dark:text-dark-warning",
  };
  return (
    <button type="button" onClick={onClick} disabled={disabled} className={clsx("font-label text-label-sm underline underline-offset-2 disabled:opacity-40", tones[tone])}>
      {children}
    </button>
  );
}