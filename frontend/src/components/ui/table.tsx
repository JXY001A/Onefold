import clsx from "clsx";
import type { ReactNode, TdHTMLAttributes, ThHTMLAttributes } from "react";

/** 表格外壳：圆角边框 + 横向滚动。 */
export function TableShell({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-md border border-light-outline-variant bg-light-surface dark:border-dark-outline-variant dark:bg-dark-surface">
      <table className="w-full text-left font-body text-body-sm text-light-on-surface dark:text-dark-on-surface">{children}</table>
    </div>
  );
}

export function THead({ children }: { children: ReactNode }) {
  return <thead className="bg-light-surface-container-low font-label text-label-sm text-light-on-surface-variant dark:bg-dark-surface-container-low dark:text-dark-on-surface-variant">{children}</thead>;
}

export function Th({ children, className, ...rest }: { children?: ReactNode } & ThHTMLAttributes<HTMLTableCellElement>) {
  return <th {...rest} className={clsx("px-gutter-md py-gutter-sm font-medium", className)}>{children}</th>;
}

export function Td({ children, className, ...rest }: { children?: ReactNode } & TdHTMLAttributes<HTMLTableCellElement>) {
  return <td {...rest} className={clsx("border-t border-light-outline-variant px-gutter-md py-gutter-sm dark:border-dark-outline-variant", className)}>{children}</td>;
}