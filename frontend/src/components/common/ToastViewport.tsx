/** 轻提示的渲染层：只负责样式与关闭按钮，状态在 ToastContext。 */
import Icon from "../ui/Icon";

export type ToastKind = "success" | "error";

export type ToastItem = { id: number; kind: ToastKind; message: string };

type Props = { items: ToastItem[]; onDismiss: (id: number) => void };

const STYLE: Record<ToastKind, string> = {
  success: "border-light-primary bg-light-primary-container text-light-on-primary-container dark:border-dark-primary dark:bg-dark-primary-container dark:text-dark-on-primary-container",
  error: "border-light-error bg-light-surface text-light-error dark:border-dark-error dark:bg-dark-surface dark:text-dark-error",
};

export default function ToastViewport({ items, onDismiss }: Props) {
  return (
    <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4" aria-live="polite">
      {items.map((item) => (
        <div
          key={item.id}
          role={item.kind === "error" ? "alert" : "status"}
          className={`toast-in pointer-events-auto flex w-full max-w-md items-start gap-gutter-sm rounded-md border px-gutter-md py-gutter-sm font-body text-body-sm shadow-lg ${STYLE[item.kind]}`}
        >
          <Icon name={item.kind === "error" ? "error" : "check_circle"} size={18} className="mt-0.5 shrink-0" />
          <span className="flex-1 leading-relaxed">{item.message}</span>
          <button type="button" onClick={() => onDismiss(item.id)} aria-label="关闭提示" className="shrink-0 rounded px-1 opacity-60 transition hover:opacity-100">
            <Icon name="close" size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}