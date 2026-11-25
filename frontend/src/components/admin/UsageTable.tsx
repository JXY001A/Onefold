import type { UsageRow } from "../../lib/admin";
import { EmptyText } from "../ui/kit";
import { TableShell, Td, Th, THead } from "../ui/table";

/** 每日用量：按用户 + 日期一行，管理员用来核对 token 消耗。 */
export default function UsageTable({ rows }: { rows: UsageRow[] }) {
  return (
    <TableShell>
      <THead>
        <tr>
          <Th>用户</Th>
          <Th>日期</Th>
          <Th>消息</Th>
          <Th>输入 token</Th>
          <Th>输出 token</Th>
          <Th>工具调用</Th>
        </tr>
      </THead>
      <tbody>
        {rows.map((u) => (
          <tr key={`${u.user_id}-${u.day}`}>
            <Td className="font-mono text-mono-sm">{u.user_id}</Td>
            <Td>{u.day}</Td>
            <Td className="tabular-nums">{u.messages}</Td>
            <Td className="tabular-nums">{u.tokens_in}</Td>
            <Td className="tabular-nums">{u.tokens_out}</Td>
            <Td className="tabular-nums">{u.tool_calls}</Td>
          </tr>
        ))}
      </tbody>
      {rows.length === 0 && <tbody><tr><Td colSpan={6}><EmptyText className="py-gutter-md">暂无用量。</EmptyText></Td></tr></tbody>}
    </TableShell>
  );
}