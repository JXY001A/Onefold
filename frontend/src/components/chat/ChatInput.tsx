type Props = {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onStop: () => void;
  running: boolean;
  /** 身份未就绪或会话加载中时禁用输入 */
  disabled?: boolean;
};

/** 输入区：Enter 发送（Shift+Enter 换行），生成中把「发送」换成「停止」。 */
export default function ChatInput({
  value,
  onChange,
  onSend,
  onStop,
  running,
  disabled = false,
}: Props) {
  return (
    <div className="flex gap-2">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend();
          }
        }}
        disabled={running || disabled}
        placeholder={disabled ? "正在准备会话…" : "输入问题…"}
        className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-500 disabled:bg-slate-50"
      />
      {running ? (
        <button
          onClick={onStop}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
        >
          停止
        </button>
      ) : (
        <button
          onClick={onSend}
          disabled={disabled}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:bg-slate-400"
        >
          发送
        </button>
      )}
    </div>
  );
}