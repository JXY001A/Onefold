import { Link } from "react-router-dom";
import type { Role } from "../../lib/roles";
import { ROLE_LABEL } from "../../lib/roles";
import { EmptyText } from "../ui/kit";

/** 无后台权限时的提示：说清当前身份与下一步，不暴露任何数据。 */
export default function NoAccess({ role }: { role: Role | undefined }) {
  return (
    <div className="space-y-gutter-sm py-section">
      <EmptyText>你没有后台权限。当前身份：{role ? ROLE_LABEL[role] : "未识别"}。</EmptyText>
      <EmptyText>
        管理员由超管指定。如已是成员账号，请联系超管开通。
        <Link className="ml-1 text-light-primary underline dark:text-dark-primary" to="/login">登录 / 注册</Link>
      </EmptyText>
    </div>
  );
}