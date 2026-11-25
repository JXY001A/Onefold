import clsx from "clsx";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

/** 表单输入统一样式：聚焦主色描边，暗亮通用。 */
export const fieldClass =
  "w-full rounded border border-light-outline-variant bg-light-surface px-3 py-2 font-body text-body-sm text-light-on-surface outline-none transition-colors duration-state-change placeholder:text-light-outline focus:border-light-primary disabled:opacity-60 dark:border-dark-outline-variant dark:bg-dark-surface dark:text-dark-on-surface dark:placeholder:text-dark-outline dark:focus:border-dark-primary";

export function TextInput({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...rest} className={clsx(fieldClass, className)} />;
}

/** 主色实心按钮。 */
export function PrimaryButton({ children, className, ...rest }: { children: ReactNode } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...rest}
      className={clsx(
        "rounded bg-light-primary px-gutter-md py-2 font-label text-label-md text-light-on-primary transition-opacity duration-state-change hover:opacity-90 disabled:opacity-40 dark:bg-dark-primary dark:text-dark-on-primary",
        className,
      )}
    >
      {children}
    </button>
  );
}

/** 描边幽灵按钮。 */
export function GhostButton({ children, className, ...rest }: { children: ReactNode } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...rest}
      className={clsx(
        "rounded border border-light-outline-variant px-gutter-md py-2 font-label text-label-md text-light-on-surface transition-colors duration-state-change hover:bg-light-surface-container-high disabled:opacity-50 dark:border-dark-outline-variant dark:text-dark-on-surface dark:hover:bg-dark-surface-container-high",
        className,
      )}
    >
      {children}
    </button>
  );
}