import { Link } from "react-router-dom";

type Props = {
  used: number;
  limit: number;
  /** 后端已确认用完（403），或按次数算已经用满 */
  exhausted: boolean;
};

/** 游客配额提示：还剩多少轮；用完就地引导注册。 */
export default function QuotaBar({ used, limit, exhausted }: Props) {
  if (exhausted) {
    return (
      <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800">
        游客免费体验 {limit} 轮已用完。
        <Link className="ml-1 font-medium underline" to="/login" state={{ from: "/chat" }}>
          注册后继续
        </Link>
      </div>
    );
  }

  return (
    <p className="px-1 text-xs text-slate-500">
      游客体验：已用 {used} / {limit} 轮
      <Link className="ml-2 text-slate-700 underline" to="/login" state={{ from: "/chat" }}>
        注册不限量
      </Link>
    </p>
  );
}
