import Icon from "../ui/Icon";

type Props = {
  title: string;
  desc: string;
  confirmText: string;
  onCancel: () => void;
  onConfirm: () => void;
};

/** 删除单条 / 清空全部的确认弹窗（设计稿第 5 层）。 */
export default function MemoryConfirmModal({ title, desc, confirmText, onCancel, onConfirm }: Props) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-dark-background/80 px-gutter-md"
      role="dialog"
      aria-modal="true"
      aria-labelledby="memory-confirm-title"
    >
      <div className="flex w-full max-w-[440px] flex-col gap-gutter-md rounded-lg border border-dark-outline-variant bg-dark-surface p-gutter-lg">
        <div className="flex items-start gap-gutter-sm">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-dark-surface-container text-dark-error">
            <Icon name="warning" size={20} />
          </span>
          <div className="flex flex-col gap-gutter-xs">
            <h3 id="memory-confirm-title" className="font-headline text-headline-md text-dark-on-surface">
              {title}
            </h3>
            <p className="font-body text-body-sm text-dark-on-surface-variant">{desc}</p>
          </div>
        </div>
        <div className="flex items-center justify-end gap-gutter-sm pt-gutter-xs">
          <button
            type="button"
            onClick={onCancel}
            className="rounded bg-dark-surface-container px-gutter-md py-1.5 font-label text-label-md text-dark-on-surface-variant hover:text-dark-on-surface"
          >
            取消
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded bg-dark-error px-gutter-md py-1.5 font-label text-label-md text-dark-on-error transition-opacity hover:opacity-90"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
