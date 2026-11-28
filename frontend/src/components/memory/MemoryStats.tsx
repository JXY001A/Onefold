import Icon from "../ui/Icon";

export type MemoryStatsData = {
  total: number;
  active: number;
  inactive: number;
  citations: number;
};

/** 记忆统计概览：四张紧凑统计卡。
 * 「累计引用」来自 mock，按口径带「示例」微标。 */
export default function MemoryStats({ stats }: { stats: MemoryStatsData }) {
  const cards = [
    {
      label: "全部记忆",
      value: stats.total,
      tone: "text-dark-on-surface",
      box: "bg-dark-surface-container text-dark-on-surface-variant",
      icon: "database",
      mock: false,
    },
    {
      label: "已激活",
      value: stats.active,
      tone: "text-dark-success",
      box: "bg-dark-primary-container text-dark-success",
      icon: "check_circle",
      mock: false,
    },
    {
      label: "已停用",
      value: stats.inactive,
      tone: "text-dark-outline",
      box: "bg-dark-surface-container text-dark-outline",
      icon: "do_not_disturb_on",
      mock: false,
    },
    {
      label: "累计引用",
      value: stats.citations,
      tone: "text-dark-primary",
      box: "bg-dark-primary-container text-dark-primary",
      icon: "format_quote",
      mock: true,
    },
  ];

  return (
    <section aria-label="记忆统计概览" className="grid grid-cols-2 items-stretch gap-gutter-md lg:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="flex h-full items-center justify-between gap-gutter-sm rounded border border-dark-outline-variant bg-dark-surface px-gutter-md py-gutter-sm"
        >
          <div className="flex flex-col gap-0.5">
            <span className="flex items-center gap-1 font-label text-label-sm text-dark-on-surface-variant">
              {card.label}
              {card.mock && <span className="font-mono text-[10px] text-dark-outline">示例</span>}
            </span>
            <span className={`font-headline text-headline-lg tabular-nums ${card.tone}`}>{card.value}</span>
          </div>
          <span className={`flex h-8 w-8 items-center justify-center rounded-sm ${card.box}`}>
            <Icon name={card.icon} size={18} />
          </span>
        </div>
      ))}
    </section>
  );
}
