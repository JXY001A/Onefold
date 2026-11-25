import { Link } from "react-router-dom";

type Props = {
  used: number;
  limit: number;
  exhausted: boolean;
};

/** 游客配额提示：还剩多少轮；用完就地引导注册。 */
export default function QuotaBar({ used, limit, exhausted }: Props) {
  if (exhausted) {
    return (
      <div className="mx-auto w-full max-w-[800px] rounded border border-light-warning bg-light-warning-container px-gutter-md py-gutter-sm font-body text-body-sm text-light-on-warning-container dark:border-dark-warning dark:bg-dark-warning-container dark:text-dark-on-warning-container">
        游客免费体验 {limit} 轮已用完。
        <Link className="ml-1 font-medium underline" to="/login" state={{ from: "/chat" }}>注册后继续</Link>
      </div>
    );
  }

  return (
    <p className="mx-auto w-full max-w-[800px] px-1 font-label text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
      游客体验：已用 {used} / {limit} 轮
      <Link className="ml-2 text-light-primary underline dark:text-dark-primary" to="/login" state={{ from: "/chat" }}>注册不限量</Link>
    </p>
  );
}