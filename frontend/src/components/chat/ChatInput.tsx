import Icon from "../ui/Icon";
import Soon from "../ui/Soon";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onStop: () => void;
  running: boolean;
  disabled?: boolean;
  /** 主态双行卡 / 专注 820 单行 / 展开 740 单行；三态共用同一输入控件 */
  variant?: "main" | "focus" | "expanded";
};

const ghost = "inline-flex items-center gap-1 py-1 font-label text-label-sm text-light-outline dark:text-dark-outline";

/** 研究输入区：Enter 发送 / Shift+Enter 换行；范围、附加文档、@引用尚待开放。 */
export default function ChatInput({ value, onChange, onSend, onStop, running, disabled = false, variant = "main" }: Props) {
  const inline = variant !== "main";
  const width = variant === "focus" ? "max-w-[820px]" : variant === "expanded" ? "max-w-[740px]" : "max-w-[800px]";

  return (
    <div className="shrink-0 border-t border-light-outline-variant bg-light-background px-gutter-xl py-gutter-md dark:border-dark-outline-variant dark:bg-dark-background">
      <div
        className={`mx-auto flex w-full ${width} rounded-md border border-light-outline-variant bg-light-surface transition-colors duration-state-change focus-within:border-light-primary dark:border-dark-outline-variant dark:bg-dark-surface dark:focus-within:border-dark-primary ${
          inline ? "flex-row items-center gap-gutter-md px-gutter-md py-gutter-sm" : "flex-col gap-gutter-sm p-gutter-md"
        }`}
      >
        {/* 顶行：附件芯片位与范围按钮（未实现业务，克制 Soon）；单行态隐藏 */}
        <div className={`${inline ? "hidden" : "flex"} flex-wrap items-center justify-end gap-gutter-sm`}>
          <Soon tip="检索范围随后开放">
            <span className="inline-flex items-center gap-1 rounded-sm px-2 py-0.5 font-label text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
              <Icon name="tune" size={14} />
              范围
            </span>
          </Soon>
        </div>

        <textarea
          value={value}
          rows={inline ? 1 : 2}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          disabled={running || disabled}
          placeholder={disabled ? "正在准备会话…" : "输入研究问题，或粘贴链接 / 上传文档…"}
          className={`w-full resize-none border-0 bg-transparent p-0 text-light-on-surface placeholder:text-light-outline focus:ring-0 disabled:opacity-60 dark:text-dark-on-surface dark:placeholder:text-dark-outline ${
            inline ? "font-body text-body-sm" : "font-body text-body-md"
          }`}
        />

        <div className={`${inline ? "shrink-0" : "border-t border-light-outline-variant pt-1 dark:border-dark-outline-variant"} flex items-center justify-between gap-gutter-md`}>
          {!inline && (
            <div className="flex items-center gap-gutter-md">
              <Soon tip="附加文档随后开放">
                <span className={ghost}>
                  <Icon name="attach_file" size={16} />
                  附加文档
                </span>
              </Soon>
              <Soon tip="@ 引用知识库随后开放">
                <span className={ghost}>
                  <Icon name="alternate_email" size={16} />
                  引用知识库
                </span>
              </Soon>
            </div>
          )}

          {running ? (
            <button
              type="button"
              onClick={onStop}
              className="inline-flex shrink-0 items-center gap-1 rounded-sm border border-light-outline-variant px-gutter-md py-1.5 font-label text-label-md text-light-on-surface dark:border-dark-outline-variant dark:text-dark-on-surface"
            >
              <Icon name="stop" size={15} />
              停止
            </button>
          ) : (
            <button
              type="button"
              onClick={onSend}
              disabled={disabled || !value.trim()}
              className="inline-flex shrink-0 items-center gap-1 rounded-sm bg-light-primary px-gutter-md py-1.5 font-label text-label-md text-light-on-primary transition-opacity duration-state-change hover:opacity-90 disabled:opacity-40 dark:bg-dark-primary dark:text-dark-on-primary"
            >
              发送
              {!inline && <Icon name="arrow_upward" size={15} />}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
