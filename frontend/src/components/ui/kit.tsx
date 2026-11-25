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
    <div className="flex flex-wrap items-start justify-between gap-gutter-sm">
      <div className="min-w-0 flex-1">
        <h2 className="font-headline text-headline-md text-light-on-surface dark:text-dark-on-surface">{title}</h2>
        {desc && <p className="mt-1 font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">{desc}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-gutter-sm">{actions}</div>}
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
  return <span className={clsx("whitespace-nowrap rounded-sm px-2 py-0.5 font-label text-label-sm", tones[tone])}>{children}</span>;
}

/** 空态 / 次要说明文字。 */
export function EmptyText({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={clsx("font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant", className)}>{children}</p>;
}

type TabItem = { key: string; label: string };

/**
 * 页签：下划线（后台/知识库 2.0）与分段胶囊（登录 2.0）。
 * 默认用法不影响既有 PillTabs。
 */
export function Tabs({
  tabs,
  active,
  onChange,
  variant = "underline",
  className,
}: {
  tabs: TabItem[];
  active: string;
  onChange: (key: string) => void;
  variant?: "underline" | "segmented";
  className?: string;
}) {
  if (variant === "segmented") {
    return (
      <div className={clsx("inline-flex items-center gap-1 rounded-full bg-light-surface-container-low p-1 dark:bg-dark-surface-container-low", className)}>
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => onChange(t.key)}
            className={clsx(
              "rounded-full px-gutter-md py-1 font-label text-label-sm transition-colors duration-state-change",
              active === t.key
                ? "bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary"
                : "text-light-on-surface-variant hover:bg-light-surface-container-high dark:text-dark-on-surface-variant dark:hover:bg-dark-surface-container-high",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className={clsx("flex flex-wrap items-center gap-gutter-lg border-b border-light-outline-variant dark:border-dark-outline-variant", className)}>
      {tabs.map((t) => (
        <button
          key={t.key}
          type="button"
          onClick={() => onChange(t.key)}
          className={clsx(
            "-mb-px border-b-2 pb-2 font-label text-label-md transition-colors duration-state-change",
            active === t.key
              ? "border-light-primary text-light-on-surface dark:border-dark-primary dark:text-dark-on-surface"
              : "border-transparent text-light-on-surface-variant hover:text-light-on-surface dark:text-dark-on-surface-variant dark:hover:text-dark-on-surface",
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
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