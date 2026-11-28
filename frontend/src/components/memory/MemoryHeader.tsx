import { useState } from "react";
import { useToast } from "../../context/ToastContext";
import Icon from "../ui/Icon";

type Props = {
  enabled: boolean;
  onToggleGlobal: () => void;
  /** 打开「清空全部记忆」确认弹窗（真实删除由页面执行） */
  onClearAll: () => void;
};

/** 记忆中心头部：标题/状态徽标/全局开关/新增/更多操作。
 * 全局开关为真实能力；新增记忆与导出无后端接口，按口径提示「敬请期待」。 */
export default function MemoryHeader({ enabled, onToggleGlobal, onClearAll }: Props) {
  const toast = useToast();
  const [menuOpen, setMenuOpen] = useState(false);

  const comingSoon = (what: string) => {
    setMenuOpen(false);
    toast.push("success", `${what}功能敬请期待`);
  };

  return (
    <header className="flex flex-col gap-gutter-md border-b border-dark-outline-variant pb-gutter-md lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-col gap-gutter-xs">
        <div className="flex items-center gap-gutter-sm">
          <h1 className="font-headline text-headline-lg text-dark-on-surface">记忆中心</h1>
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-gutter-sm py-0.5 font-label text-label-sm ${
              enabled
                ? "bg-dark-primary-container text-dark-on-primary-container"
                : "bg-dark-surface-container text-dark-outline"
            }`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${enabled ? "bg-dark-success" : "bg-dark-outline"}`} />
            {enabled ? "记忆已开启" : "记忆已关闭"}
          </span>
        </div>
        <p className="font-body text-body-sm text-dark-on-surface-variant">
          管理 AI 对你的了解，控制哪些信息可以参与后续对话。
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-gutter-sm">
        <div className="flex items-center gap-gutter-sm rounded border border-dark-outline-variant bg-dark-surface px-gutter-md py-gutter-sm">
          <span className="font-label text-label-md text-dark-on-surface">
            {enabled ? "记忆已开启" : "记忆已关闭"}
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={enabled}
            aria-label="全局记忆开关"
            onClick={onToggleGlobal}
            className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-state-change focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-dark-primary ${
              enabled ? "bg-dark-success" : "bg-dark-surface-container-highest"
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-3.5 w-3.5 rounded-full transition-transform duration-state-change ${
                enabled ? "translate-x-[18px] bg-dark-on-success" : "translate-x-[3px] bg-dark-on-surface-variant"
              }`}
            />
          </button>
        </div>

        <button
          type="button"
          onClick={() => comingSoon("新增记忆")}
          className="inline-flex items-center gap-gutter-xs rounded bg-dark-primary px-gutter-md py-gutter-sm font-label text-label-md text-dark-on-primary transition-opacity duration-state-change hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-dark-primary"
        >
          <Icon name="add" size={18} />
          <span>新增记忆</span>
        </button>

        <div className="relative">
          <button
            type="button"
            aria-haspopup="true"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
            className="inline-flex items-center gap-gutter-xs rounded border border-dark-outline-variant bg-dark-surface px-gutter-sm py-gutter-sm font-label text-label-md text-dark-on-surface-variant transition-colors duration-state-change hover:bg-dark-surface-container hover:text-dark-on-surface focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-dark-primary"
          >
            <Icon name="more_horiz" size={18} />
            <span>更多操作</span>
          </button>

          {menuOpen && (
            <div
              role="menu"
              className="absolute right-0 z-30 mt-gutter-xs w-44 rounded border border-dark-outline-variant bg-dark-surface-container py-gutter-xs"
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => comingSoon("导出记忆")}
                className="flex w-full items-center gap-gutter-sm px-gutter-md py-gutter-sm text-left font-label text-label-md text-dark-on-surface transition-colors duration-state-change hover:bg-dark-surface-container-high"
              >
                <Icon name="download" size={18} className="text-dark-on-surface-variant" />
                <span>导出记忆</span>
              </button>
              <div className="my-gutter-xs border-t border-dark-outline-variant" />
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setMenuOpen(false);
                  onClearAll();
                }}
                className="flex w-full items-center gap-gutter-sm px-gutter-md py-gutter-sm text-left font-label text-label-md text-dark-error transition-colors duration-state-change hover:bg-dark-surface-container-high"
              >
                <Icon name="delete_sweep" size={18} />
                <span>清空全部记忆</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
