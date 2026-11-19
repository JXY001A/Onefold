import { useCallback, useEffect, useState } from "react";
import RequestTable from "../components/admin/RequestTable";
import NoAccess from "../components/admin/NoAccess";
import UsageTable from "../components/admin/UsageTable";
import UserTable from "../components/admin/UserTable";
import { useAuth } from "../context/AuthContext";
import {
  approveRequest,
  changeRole,
  changeStatus,
  fetchRequests,
  fetchUsage,
  fetchUsers,
  type AccessRequest,
  type AdminUser,
  type UsageRow,
} from "../lib/admin";
import { canManageUsers, canUseAdmin } from "../lib/roles";

type Tab = "users" | "requests" | "usage";

const TABS: { key: Tab; label: string }[] = [
  { key: "users", label: "用户" },
  { key: "requests", label: "体验码申请" },
  { key: "usage", label: "用量" },
];

/** 后台：先按角色守卫，再按标签页展示；写操作只有超管能点。 */
export default function Admin() {
  const { me, loading } = useAuth();
  const [tab, setTab] = useState<Tab>("users");
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [usage, setUsage] = useState<UsageRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allowed = canUseAdmin(me?.role);
  const canManage = canManageUsers(me?.role);

  const reload = useCallback(async () => {
    const [u, r, g] = await Promise.all([fetchUsers(), fetchRequests(), fetchUsage()]);
    setUsers(u);
    setRequests(r);
    setUsage(g);
  }, []);

  useEffect(() => {
    if (!allowed) return;
    let cancelled = false;
    reload().catch((e) => {
      if (!cancelled) setError((e as Error).message);
    });
    return () => {
      cancelled = true;
    };
  }, [allowed, reload]);

  /** 统一「请求 → 报错 → 重新加载」，busy 期间禁用按钮防连点 */
  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <p className="py-10 text-sm text-slate-500">加载中…</p>;
  if (!allowed) return <NoAccess role={me?.role} />;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2 text-sm">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-lg px-3 py-1.5 ${
              tab === t.key ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {t.label}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-400">
          {canManage ? "超管：可改角色与停用账号" : "管理员：只读"}
        </span>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {tab === "users" && (
        <UserTable
          users={users}
          canManage={canManage}
          busy={busy}
          onRole={(id, role) => void run(() => changeRole(id, role))}
          onStatus={(id, status) => void run(() => changeStatus(id, status))}
        />
      )}
      {tab === "requests" && (
        <RequestTable
          requests={requests}
          busy={busy}
          onApprove={(id) => void run(() => approveRequest(id))}
        />
      )}
      {tab === "usage" && <UsageTable rows={usage} />}
    </div>
  );
}
