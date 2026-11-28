# Onefold 容器与主机监控实施方案（Beszel）

> 状态：已实施并在生产验证（`https://monitor.mindbase.ink`）。
> 定位：个人项目的轻量可观测性，不引入 Prometheus/Grafana 体系，不侵入 AI 实验主线。
> 原则：监控失败不影响主站发布；不暴露多余公网端口；密钥只存服务器 `.env`。

## 1. 目标与非目标

目标：
- 看到 app、memory-worker、index-worker、db、caddy 的存活与资源占用；
- 看到宿主机 CPU/内存/网络（磁盘需额外挂载，见 §9）；
- worker「进程活着但循环卡死」也能被发现；
- 部署后自动启动监控，服务器重启自动拉起；
- 通过独立子域名 HTTPS 访问，无需每天开隧道。

非目标：
- 不做多租户、日志平台、链路追踪、复杂告警编排；
- 不替换 Onefold 自身的管理后台；
- 不做 7×24 值班与 SLA。

## 2. 文字版架构图

```text
                        你的浏览器
                            │ HTTPS 443
                            ▼
                  onefold-caddy-1（Caddy）
        ┌───────────────────┴────────────────────┐
        │ mindbase.ink                           │ monitor.mindbase.ink
        ▼                                        ▼
 onefold-app-1 (FastAPI)                 onefold-beszel-1 (Hub)
 127.0.0.1:8000                          127.0.0.1:8090
        │                                        ▲
        │ /healthz                               │ 共享 Unix socket
        │                                        │ /beszel_socket/beszel.sock
        │                               onefold-beszel-agent-1
        │                               （host 网络）
        │                                  ├─ /var/run/docker.sock（只读）
        │                                  ├─ 宿主 CPU / 内存 / 网络
        │                                  └─ 容器列表与资源
        ▼
 ┌───────────────┬────────────────┬─────────────────┬──────────────┐
 │ memory-worker │ index-worker   │ db (pgvector)   │ 数据卷 ./data │
 └───────────────┴────────────────┴─────────────────┴──────────────┘
        │                │
        │ 每 10s touch   │ 每 10s touch
        ▼                ▼
 /tmp/onefold-worker-alive（各自容器内）
        │
        ▼
 Docker healthcheck：文件 60s 未更新 → unhealthy

数据流：
浏览器 → Caddy → Hub（看板/告警）
Hub ⇄ Agent（Unix socket）→ Docker socket / 宿主指标
worker → 心跳文件 → Docker healthcheck
app → /healthz → Docker healthcheck
```

## 3. 组件与端口

| 服务 | 镜像/入口 | 端口 | 作用 |
|---|---|---|---|
| onefold-app-1 | Onefold 镜像，FastAPI | `127.0.0.1:8000` | 业务 API，`/healthz` 健康检查 |
| onefold-memory-worker-1 | `python -m app.workers.memory` | 无 | 记忆提取；写心跳文件 |
| onefold-index-worker-1 | `python -m app.workers.document_index` | 无 | 文档解析/索引；写心跳文件 |
| onefold-db-1 | `pgvector/pgvector:pg16` | 内部 5432 | 业务数据库 |
| onefold-caddy-1 | `caddy:2` | 80/443 | 主站与监控子域名反代 |
| onefold-beszel-1 | `henrygd/beszel:0.21.1` | `127.0.0.1:8090` | 监控 Hub/存储/告警 |
| onefold-beszel-agent-1 | `henrygd/beszel-agent:0.21.1` | 无（Unix socket） | 采集宿主与容器指标 |

数据卷：`beszel_data`（Hub 数据）、`beszel_socket`（Hub/Agent 共享 socket）、`beszel_agent_data`（Agent 数据）。

## 4. 代码与配置改动

| 文件 | 改动 |
|---|---|
| `backend/app/workers/runner.py` | 新增心跳线程：每 10s 刷新 `/tmp/onefold-worker-alive`，收到停止信号退出；写失败仅告警 |
| `docker-compose.yml` | ① 两个 worker 增加 healthcheck（60s 未更新即 unhealthy）；② 新增 `beszel`/`beszel-agent`（`profiles: ["obs"]`）；③ 新增 3 个命名卷；④ Caddy 注入 `MONITOR_DOMAIN` |
| `Caddyfile` | 新增 `{$MONITOR_DOMAIN}` 站点，反代 `beszel:8090`；主站 SSE 配置不变 |
| `deploy.sh` | 读取 `.env` 的可选监控配置；部署后显式 reload Caddy；主站探活成功后启动 obs（失败只告警，不影响主站） |
| `.env.example` | 增加监控变量模板；`.env.example` 不参与运行 |

关键设计：
- Hub 只绑定 `127.0.0.1:8090`，公网仅通过 Caddy 443；
- Agent 使用 `network_mode: host` + 共享 Unix socket，不发布 45876；
- `HUB_URL` 固定 `http://127.0.0.1:8090`，避免 host 网络下 localhost 解析到 IPv6；
- 监控服务使用 `restart: unless-stopped`，服务器重启自动拉起。

## 5. 服务器 `.env` 变量

```dotenv
MONITOR_DOMAIN=monitor.mindbase.ink
ENABLE_OBS=true

BESZEL_VERSION=0.21.1
BESZEL_ADMIN_EMAIL=你的邮箱          # 仅全新 beszel_data 生效
BESZEL_ADMIN_PASSWORD=至少10位密码

# agent 接入二选一：
# 1) Universal Token：只填 TOKEN
# 2) Add System：KEY + TOKEN 都填
BESZEL_AGENT_KEY=
BESZEL_AGENT_TOKEN=
```

密钥只写服务器 `.env`，不提交 Git；`/api` 与业务表不受监控影响。

## 6. 首次部署流程

1. DNS：`monitor.mindbase.ink` A 记录 → 服务器公网 IP；
2. 同步代码与运维文件；确保新镜像包含 worker 心跳；
3. `.env` 填 §5 变量（agent 令牌先留空）；
4. 执行 `./deploy.sh`：
   - 备份 DB → 拉镜像 → 迁移检查 → `up -d` → **Caddy reload** → 主站探活；
   - 探活成功后启动 `beszel`；无 agent 令牌时跳过 agent；
5. 打开 `https://monitor.mindbase.ink`，登录/注册管理员；
6. Settings → Tokens 生成 **Universal Token**，写入 `.env` 的 `BESZEL_AGENT_TOKEN`；
7. 执行 `docker compose --profile obs up -d --force-recreate beszel-agent`（或再跑一次 `deploy.sh`）；
8. 面板出现系统与容器列表。

## 7. 日常判读

- `Healthy`：healthcheck 通过；
- `None`：该容器没有配置 healthcheck（Beszel Hub/Agent/Caddy），`Up` 即正常；
- worker `Unhealthy`：心跳 60s 未更新，进程卡死/异常，查 `docker compose logs --tail=100 <worker>`；
- `Restarting`：进程反复退出；看日志与环境变量；
- Uptime 突然变小：容器重启；
- 空闲时 CPU 0%、网络 0 B/s 正常，不代表卡死。

## 8. 自动化边界

已自动：
- 服务器重启拉起全部容器；
- 每次 `deploy.sh` 重载 Caddy、确保监控启动；
- 管理员首次创建（新数据卷 + 环境变量）；
- Agent 断线自动重连（`restart: unless-stopped`）。

保留一次手动：
- Universal Token 必须在 Hub 生成一次；这是凭据签发，不建议逆向 API 自动化（脆弱且高风险）。

## 9. 已知限制

1. **磁盘**：Docker 内 Agent 默认可能只看到容器/挂载目录的文件系统；要监控宿主根盘或数据盘，需增加只读挂载：
```yaml
beszel-agent:
  volumes:
    - ./data:/extra-filesystems/onefold-data:ro
  environment:
    EXTRA_FILESYSTEMS: onefold-data
```
2. **网络**：已通过 host 网络采集；若改成 bridge，网络指标会缺失。
3. **Hub 自身宕机**：本地监控无法通知自己；需要外部探活（Uptime Kuma/Healthchecks）时再加。
4. **日志**：不提供日志搜索；临时排查用 `docker compose logs`，需要 UI 可后续加 Dozzle。
5. **权限**：`docker.sock` 只读挂载仍具备较高权限，Beszel 账号需强密码。

## 10. 回滚

```bash
# 关闭自动监控，主站不受影响
sed -i 's/^ENABLE_OBS=.*/ENABLE_OBS=false/' .env
./deploy.sh

# 或直接停监控
docker compose --profile obs stop beszel beszel-agent
```

- 监控子域名会 502，但主站正常；
- 数据卷保留，重新启用即可恢复；
- worker 心跳与 healthcheck 可单独回退，不改任务逻辑，无数据库迁移。

## 11. 成本

- Hub 约 11 MB、Agent 约 3.4 MB 内存；CPU 近 0%；
- 无额外云服务与付费依赖；
- 子域名无新增费用（已有 `mindbase.ink`），Caddy 自动 HTTPS。

## 12. 后续升级（按需）

1. 宿主磁盘/数据盘挂载与告警；
2. Beszel 邮件/Webhook 通知；
3. 外部探活（防止 Hub 自身宕机）；
4. Dozzle 日志面板；
5. 只有需要跨天趋势与自定义指标时，再评估 Prometheus/Grafana。
