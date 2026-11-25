import { useCallback, useEffect, useState } from "react";
import NoAccess from "../components/admin/NoAccess";
import UsageTable from "../components/admin/UsageTable";
import UserTable from "../components/admin/UserTable";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import {
  changeRole,
  changeStatus,
  fetchUsage,
  fetchUsers,
  type AdminUser,
  type UsageRow,
} from "../lib/admin";
import { canManageUsers, canUseAdmin } from "../lib/roles";
import { EmptyText, PillTabs } from "../components/ui/kit";

type Tab = "users" | "usage";

const TABS: { key: Tab; label: string }[] = [
  { key: "users", label: "用户" },
  { key: "usage", label: "用量" },
];

/** 后台：先按角色守卫，再按标签页展示；写操作只有超管能点。 */
export default function Admin() {
  const { me, loading } = useAuth();
  const toast = useToast();
  const [tab, setTab] = useState<Tab>("users");
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [usage, setUsage] = useState<UsageRow[]>([]);
  const [busy, setBusy] = useState(false);

  const allowed = canUseAdmin(me?.role);
  const canManage = canManageUsers(me?.role);

  const reload = useCallback(async () => {
    const [u, g] = await Promise.all([fetchUsers(), fetchUsage()]);
    setUsers(u);
    setUsage(g);
  }, []);

  useEffect(() => {
    if (!allowed) return;
    let cancelled = false;
    reload().catch((e) => {
      if (!cancelled) toast.push("error", (e as Error).message);
    });
    return () => {
      cancelled = true;
    };
  }, [allowed, reload, toast]);

  /** 统一「请求 → 提示 → 重新加载」，busy 期间禁用按钮防连点 */
  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await fn();
      await reload();
    } catch (e) {
      toast.push("error", (e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <EmptyText className="py-section">加载中…</EmptyText>;
  if (!allowed) return <NoAccess role={me?.role} />;

  return (
    <div className="space-y-gutter-md">
      <div className="flex flex-wrap items-center justify-between gap-gutter-sm">
        <PillTabs tabs={TABS} active={tab} onChange={(k) => setTab(k as Tab)} />
        <span className="font-label text-label-sm text-light-outline dark:text-dark-outline">
          {canManage ? "超管：可改角色与停用账号" : "管理员：只读"}
        </span>
      </div>

      {tab === "users" && (
        <UserTable
          users={users}
          canManage={canManage}
          busy={busy}
          onRole={(id, role) => void run(() => changeRole(id, role))}
          onStatus={(id, status) => void run(() => changeStatus(id, status))}
        />
      )}
      {tab === "usage" && <UsageTable rows={usage} />}
    </div>
  );
}
