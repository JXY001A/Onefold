import { useEffect, useRef } from "react";
import type { ChatMessage } from "../../lib/chat";
import Icon from "../ui/Icon";
import BrandMark from "../layout/BrandMark";
import MessageItem from "./MessageItem";

type Props = {
  messages: ChatMessage[];
  status?: string;
  error?: string | null;
  /** 点击空态示例问题：回填到输入框 */
  onPick?: (text: string) => void;
  /** 专注阅读模式：更宽的居中画布 */
  focus?: boolean;
  /** 检查器展开态：更窄的居中画布 */
  expanded?: boolean;
};

const EXAMPLES = [
  "对比混合检索与纯向量检索在中文长文档上的召回率",
  "总结团队公共白皮书的核心结论与风险点",
  "把这份访谈纪要整理成结构化研究笔记",
];

/** 研究画布：居中限宽的编辑式报告流，新内容自动滚到底部。 */
export default function MessageList({ messages, status, error, onPick, focus = false, expanded = false }: Props) {
  const endRef = useRef<HTMLDivElement>(null);
  const tail = messages[messages.length - 1];

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages.length, tail?.content, status, error]);

  const width = expanded ? "max-w-[740px] gap-gutter-lg px-gutter-lg py-gutter-lg" : focus ? "max-w-[820px] gap-gutter-xl px-gutter-xl py-gutter-xl" : "max-w-[800px] gap-gutter-lg px-gutter-xl py-gutter-lg";

  return (
    // 窄屏随整页滚动，lg 及以上保持画布内独立滚动
    <div className="lg:h-full lg:overflow-y-auto">
      <div className={`mx-auto flex w-full flex-col ${width}`}>
        {messages.length === 0 && (
          <div className="flex flex-col items-center gap-gutter-md py-section text-center">
            <BrandMark className="h-12 w-12" />
            <h2 className="font-headline text-headline-md text-light-on-surface dark:text-dark-on-surface">开始一项研究</h2>
            <p className="max-w-[420px] font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
              提出一个问题，归一会检索知识库与联网来源，生成带工具痕迹的研究报告。
            </p>
            <div className="mt-gutter-sm flex w-full max-w-[520px] flex-col gap-gutter-sm">
              {EXAMPLES.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => onPick?.(q)}
                  className="flex items-center gap-gutter-sm rounded border border-light-outline-variant bg-light-surface px-gutter-md py-gutter-sm text-left font-body text-body-sm text-light-on-surface-variant transition-colors duration-state-change hover:border-light-primary hover:text-light-on-surface dark:border-dark-outline-variant dark:bg-dark-surface dark:text-dark-on-surface-variant dark:hover:border-dark-primary dark:hover:text-dark-on-surface"
                >
                  <Icon name="arrow_forward" size={15} className="text-light-primary dark:text-dark-primary" />
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <MessageItem key={i} message={m} focus={focus} expanded={expanded} />
        ))}

        {status && <p className="text-center font-label text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">{status}</p>}
        {error && <p className="text-center font-label text-label-sm text-light-error dark:text-dark-error">{error}</p>}

        <div ref={endRef} />
      </div>
    </div>
  );
}