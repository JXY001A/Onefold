import clsx from "clsx";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

/** 表单输入统一样式：40px 高、聚焦主色描边，暗亮通用。 */
export const fieldClass =
  "h-10 w-full rounded border border-light-outline-variant bg-light-surface px-gutter-md py-2 font-body text-body-sm text-light-on-surface outline-none transition-colors duration-state-change placeholder:text-light-outline focus:border-light-primary disabled:opacity-60 dark:border-dark-outline-variant dark:bg-dark-surface dark:text-dark-on-surface dark:placeholder:text-dark-outline dark:focus:border-dark-primary";

/** 带可见 label 的字段容器（2.0 表单规范）。 */
export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block font-label text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">{label}</span>
      {children}
    </label>
  );
}

export function TextInput({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...rest} className={clsx(fieldClass, className)} />;
}

/** 主色实心按钮（40px）。 */
export function PrimaryButton({ children, className, ...rest }: { children: ReactNode } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...rest}
      className={clsx(
        "h-10 rounded-sm bg-light-primary px-gutter-md py-2 font-label text-label-md text-light-on-primary transition-opacity duration-state-change hover:opacity-90 disabled:opacity-40 dark:bg-dark-primary dark:text-dark-on-primary",
        className,
      )}
    >
      {children}
    </button>
  );
}

/** 描边幽灵按钮（40px）。 */
export function GhostButton({ children, className, ...rest }: { children: ReactNode } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...rest}
      className={clsx(
        "h-10 rounded-sm border border-light-outline-variant px-gutter-md py-2 font-label text-label-md text-light-on-surface transition-colors duration-state-change hover:bg-light-surface-container-high disabled:opacity-50 dark:border-dark-outline-variant dark:text-dark-on-surface dark:hover:bg-dark-surface-container-high",
        className,
      )}
    >
      {children}
    </button>
  );
}