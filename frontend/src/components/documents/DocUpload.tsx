import { useState, type ChangeEvent, type DragEvent } from "react";
import Icon from "../ui/Icon";

const ACCEPT = ".pdf,.md,.markdown,.txt";

/** 上传按钮：默认页头主色；拖拽区内使用白底「选择文件」。 */
export function UploadButton({
  onFile,
  disabled = false,
  label = "上传至个人知识库",
  primary = false,
}: {
  onFile: (file: File) => void;
  disabled?: boolean;
  label?: string;
  primary?: boolean;
}) {
  const pick = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFile(file);
    e.target.value = "";
  };
  const tone = primary
    ? "border-light-primary bg-light-primary text-light-on-primary hover:opacity-90 dark:border-dark-primary dark:bg-dark-primary dark:text-dark-on-primary"
    : "border-light-outline-variant text-light-on-surface hover:bg-light-surface-container-high dark:border-dark-outline-variant dark:text-dark-on-surface dark:hover:bg-dark-surface-container-high";
  return (
    <label className={`inline-flex items-center gap-1.5 rounded border px-gutter-md py-2 font-label text-label-md transition-colors ${tone} ${disabled ? "cursor-not-allowed opacity-40" : "cursor-pointer"}`}>
      <Icon name="upload_file" size={16} />
      {label}
      <input type="file" accept={ACCEPT} className="hidden" disabled={disabled} onChange={pick} />
    </label>
  );
}

/** 拖拽上传区：复用现有单文件上传接口，不新增后端能力。 */
export default function DocUpload({ onFile, disabled = false }: { onFile: (file: File) => void; disabled?: boolean }) {
  const [over, setOver] = useState(false);

  const drop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setOver(false);
    if (disabled) return;
    const file = e.dataTransfer.files?.[0];
    if (file) onFile(file);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={drop}
      className={`flex flex-wrap items-center gap-gutter-md rounded border border-dashed px-gutter-md py-gutter-md transition-colors ${
        over
          ? "border-light-primary bg-light-primary-container/40 dark:border-dark-primary dark:bg-dark-primary-container/40"
          : "border-light-outline-variant bg-light-surface dark:border-dark-outline-variant dark:bg-dark-surface"
      } ${disabled ? "opacity-60" : ""}`}
    >
      <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded bg-light-surface-container-high text-light-primary dark:bg-dark-surface-container-high dark:text-dark-primary">
        <Icon name="upload_file" size={20} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-label text-label-md text-light-on-surface dark:text-dark-on-surface">拖拽 PDF / Markdown / TXT 至此，或选择本地文件</p>
        <p className="mt-0.5 font-label text-label-sm text-light-outline dark:text-dark-outline">流水线：上传 → 解析 → Embedding → Ready</p>
      </div>
      <UploadButton onFile={onFile} disabled={disabled} label="选择文件" />
    </div>
  );
}
