import type { MemoryItem } from "../../lib/memory";
import { ActionLink, Badge, Card } from "../ui/kit";

type Props = {
  item: MemoryItem;
  onEdit: (item: MemoryItem) => void;
  onRemove: (item: MemoryItem) => void;
};

/** 单条记忆：分类/来源等元信息在上，正文在下，操作放在末尾。 */
export default function MemoryCard({ item, onEdit, onRemove }: Props) {
  return (
    <Card className="p-gutter-md">
      <div className="mb-1 flex items-center gap-gutter-sm font-label text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
        {/* 分类统一用中文，兼容后端归一化后的值；空值兜底也用中文 */}
        <Badge>{item.category ?? "其他"}</Badge>
        {item.mention_count > 1 && <span>提到 {item.mention_count} 次</span>}
        {item.pinned && <Badge tone="primary">已固定</Badge>}
      </div>
      <p className="whitespace-pre-wrap font-body text-body-sm text-light-on-surface dark:text-dark-on-surface">{item.text}</p>
      <div className="mt-gutter-sm flex gap-gutter-md">
        <ActionLink onClick={() => onEdit(item)}>编辑</ActionLink>
        <ActionLink tone="danger" onClick={() => onRemove(item)}>删除</ActionLink>
      </div>
    </Card>
  );
}