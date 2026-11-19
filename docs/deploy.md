# 部署手册

一条链路：`push main` → GitHub Actions 构建镜像并推阿里云 ACR → SSH 到服务器执行 `deploy.sh` → `docker compose pull && up -d` → 探活失败自动回滚。

```
服务器（阿里云轻量）
  Caddy :443 ──反代──> app :8000（只绑 127.0.0.1）
                         ├──> db :5432（仅容器内网，卷 pg_data）
                         └──> /data（卷 ./data：上传文件、备份）
```

---

## 0. 需要准备的信息 → 填到哪里

所有值都**不需要写进代码**，按这张表填即可。

| 信息 | 从哪来 | 填到哪 |
|---|---|---|
| 镜像仓库命名空间 | ACR 控制台 → 命名空间 | GitHub 仓库 **Variables**：`ACR_NAMESPACE`（必填） |
| 镜像仓库地址 | ACR 控制台 → 访问凭证页的示例命令 | **Variables/Secrets**：`ACR_REGISTRY`（**必填**。旧版个人版是 `registry.cn-shanghai.aliyuncs.com`；新版是 `crpi-xxx.cn-shanghai.personal.cr.aliyuncs.com`，照抄控制台，别猜） |
| ACR 用户名 / 固定密码 | ACR → 访问凭证 → 设置固定密码 | **Secrets**：`ACR_USERNAME` / `ACR_PASSWORD` |
| 服务器公网 IP | 轻量控制台 | **Secrets**：`SSH_HOST` |
| SSH 用户（`root`） | 轻量控制台 | **Secrets**：`SSH_USER` |
| SSH 私钥 | 本地 `~/.ssh/id_ed25519` 内容 | **Secrets**：`SSH_KEY` |
| 域名 | 已备案域名 | 服务器 `.env`：`ONEFOLD_DOMAIN` |
| DeepSeek Key | platform.deepseek.com | 服务器 `.env`：`API_KEY` |
| SMTP 授权码 | QQ/163 邮箱设置里生成 | 服务器 `.env`：`SMTP_*` |

GitHub 路径：仓库 → Settings → Secrets and variables → Actions，**Variables** 和 **Secrets** 是两个不同的页签。

公钥要加到服务器：`~/.ssh/authorized_keys`（`ssh-copy-id` 或手动追加）。

---

## 1. 服务器初始化（一次性）

### 1.1 系统与 Docker

```bash
apt update && apt install -y curl ca-certificates
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
docker compose version   # 需要 v2，输出 Docker Compose version v2.x
```

> 轻量服务器请用**系统镜像**（Ubuntu 22.04 / Debian 12）。如果买的是宝塔之类的应用镜像，80/443 会被占用，建议先重置为系统镜像。
> **不要在这台机器上构建镜像**：`npm ci` + `pip install` 在 2G 内存上容易 OOM，构建全部在 CI 完成。

### 1.2 防火墙（轻量控制台，不在系统里配）

控制台 → 服务器 → 防火墙 → 添加规则：

| 端口 | 协议 | 用途 |
|---|---|---|
| 22 | TCP | SSH（通常已开） |
| 80 | TCP | HTTP（Caddy 申请证书、跳转 HTTPS） |
| 443 | TCP | HTTPS |

不要再额外开 `ufw`，两层拦截很难排查。

### 1.3 放 4 个配置文件

```bash
mkdir -p /opt/onefold && cd /opt/onefold
# 从仓库取这 4 个文件（仓库私有则用 scp 从本地上传）
#   docker-compose.yml  Caddyfile  deploy.sh  .env（下一步创建）
chmod +x deploy.sh
cd /opt/onefold && ls   # 确认 4 个文件都在
```

`deploy.sh` 依赖宿主机 `curl` 做探活（`apt install -y curl` 已装）。

### 1.4 登录镜像仓库（一次，凭据长期有效）

```bash
# 地址必须用控制台「访问凭证」页给的那个（新版个人版是 crpi-xxx.<region>.personal.cr.aliyuncs.com）
docker login <ACR 地址> -u <ACR 用户名>
# 密码填 ACR 的「固定密码」，不是阿里云登录密码
```

CI 通过 SSH 以同一用户执行，会复用这份凭据。

---

## 2. 生产 `.env`

`/opt/onefold/.env`（compose 会自动读同目录 `.env` 做变量替换）：

```bash
ENV=prod
JWT_SECRET=<openssl rand -hex 32 的输出>
COOKIE_SECURE=true

# 站点域名：Caddy 据此自动申请 HTTPS 证书
ONEFOLD_DOMAIN=onefold.example.com

# 镜像地址：deploy.sh 手工执行时从这里取镜像名（CI 会另外传入，二者一致即可）
ONEFOLD_IMAGE=<ACR 地址>/<命名空间>/onefold

# 数据库密码：只在「卷首次初始化」时生效，之后改这里不会改库内密码
POSTGRES_PASSWORD=<强随机>

API_KEY=<DeepSeek 生产 key>
SEARCH_ENABLED=true

SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=<发信邮箱>
SMTP_PASSWORD=<授权码，不是登录密码>
SMTP_FROM=<同 SMTP_USER>
SMTP_SSL=true

GUEST_MAX_ROUNDS=20
```

生成随机值：

```bash
openssl rand -hex 32   # JWT_SECRET
openssl rand -base64 24 | tr -d '/+=' # POSTGRES_PASSWORD
```

要点：
- `ENV=prod` 且 `JWT_SECRET` 仍是 `change-me` 时，应用**拒绝启动**（防伪造 JWT）
- `COOKIE_SECURE=true` 要求 HTTPS，域名没配好之前登录态会写不进去
- `ONEFOLD_DOMAIN` 只写域名，**不带 `https://`**
- 已经初始化过数据库卷后再改 `POSTGRES_PASSWORD`，需要在库里 `ALTER USER onefold PASSWORD '...'`，否则应用连不上
- 改完 `.env` 要重启才生效：`docker compose up -d`（compose 会重建带新环境变量的容器）

---

## 3. 首次部署

前提：`.env` 已写好、`docker login` 已完成、GitHub 的 Variables/Secrets 已配好。

**方式 A（推荐）：让 CI 完成首次部署**

```bash
git push origin main     # 触发 build → push ACR → ssh deploy.sh
```

GitHub → Actions → deploy，两个 job 都绿即可。首次 `deploy.sh` 里 `pg_dump` 会因为 db 还没起来而失败，脚本已用 `|| true` 跳过，属正常。

**方式 B：服务器手动首次拉起**

```bash
cd /opt/onefold
TAG=latest ONEFOLD_IMAGE=<ACR 地址>/<命名空间>/onefold ./deploy.sh
```

**验收**

```bash
curl -fsS https://<域名>/healthz
# {"status":"ok","app":"onefold","env":"prod"}

curl -fsS -o /dev/null -w '%{http_code}\n' https://<域名>/chat   # 200，刷新子页面不 404
curl -fsS -o /dev/null -w '%{http_code}\n' http://<域名>          # 308，自动跳 HTTPS
```

国内服务器 80/443 必须已备案，否则会被运营商拦截（证书也签不下来）。

---

## 4. 建第一个超管

不建就没人能进 `/admin`。密码用 argon2 哈希，不要手写明文。

```bash
cd /opt/onefold

# 1) 生成密码哈希（容器里已有 passlib）
docker compose exec app python - <<'PY'
from passlib.context import CryptContext
print(CryptContext(schemes=["argon2"]).hash("<你的密码>"))
PY

# 2) 写入账号（把 <哈希> / <邮箱> 换成实际值）
docker compose exec db psql -U onefold -d onefold -c \
"INSERT INTO users (id, username, email, password_hash, role, status, created_at)
 VALUES (gen_random_uuid()::text, 'admin', '<邮箱>', '<哈希>', 'superadmin', 'active', now());"
```

之后用邮箱 + 密码登录 `/login`，`/admin` 可见审批、用户列表、用量。

---

## 5. 日常运维

| 操作 | 命令 |
|---|---|
| 发版 | `push` 到 main，或 Actions 里手动 `Run workflow` |
| 看服务状态 | `cd /opt/onefold && docker compose ps` |
| 看应用日志 | `docker compose logs -f --tail=200 app` |
| 看 Caddy（证书/转发） | `docker compose logs -f --tail=200 caddy` |
| 重启应用 | `docker compose restart app`（只是重启，不重读 .env） |
| 改了 `.env` | `cd /opt/onefold && ./deploy.sh`（环境变量要重建容器，restart 不生效） |
| 回滚到上一个版本 | 部署失败时 `deploy.sh` 会自动回滚；手动回滚见下 |
| 当前部署的版本 | `cat /opt/onefold/.current_tag` |

> 修改 `.env` 后直接跑 `./deploy.sh` 即可：它会从 `.current_tag` 和 `.env` 的 `ONEFOLD_IMAGE` 兜底镜像名与版本，并做备份 + 健康检查。
> 不要用裸的 `docker compose up -d`：会试图本地构建镜像并退化成 `onefold:latest`，报 `No such image`。

手动回滚：

```bash
cd /opt/onefold
docker images | grep onefold            # 找可用的 sha tag
TAG=<旧 sha> ONEFOLD_IMAGE=<镜像仓库地址>/onefold ./deploy.sh
```

镜像 tag 用 `sha` + `latest` 双推，`sha` 用于精确回滚。

---

## 6. 备份与恢复

`deploy.sh` 每次部署前会 `pg_dump` 到 `/opt/onefold/data/backup/`，但只在部署时执行，不够。

每日定时备份（14 天保留）：

```bash
cat >/etc/cron.d/onefold-backup <<'EOF'
30 3 * * * root cd /opt/onefold && docker compose exec -T db pg_dump -U onefold onefold | gzip > backup/onefold-$(date +\%F).sql.gz && find backup -name '*.sql.gz' -mtime +14 -delete
EOF
```

```bash
mkdir -p /opt/onefold/backup   # 放在 data/ 之外：data 会整体挂进容器，备份文件会被当成业务数据统计
```

恢复：

```bash
cd /opt/onefold
docker compose stop app
gunzip -c backup/onefold-2026-11-19.sql.gz | docker compose exec -T db psql -U onefold -d onefold
docker compose start app
```

同机备份挡不住磁盘损坏，建议再加一层：`rsync -a /opt/onefold/backup/ 本地机器:/backups/onefold/`，或推到 OSS。

上传文件在 `/opt/onefold/data/uploads`，一并纳入备份。

---

## 7. 排查手册

| 现象 | 原因与处理 |
|---|---|
| CI `docker login` 失败 | ACR 用户名应填**阿里云账号全名**，密码是「固定密码」而不是登录密码 |
| Actions 报「缺少仓库变量 ACR_NAMESPACE」 | Variables 页签里补上，注意不是 Secrets |
| 部署显示成功但页面没变 | 检查 SSH 脚本里传的 `ONEFOLD_IMAGE` 是否完整；`docker compose ps` 看 app 的镜像 tag 是否为新 sha |
| `pull access denied` | 服务器没 `docker login`，或 `ACR_REGISTRY` 与实际仓库地址不一致 |
| `docker login` 报 **403 Forbidden** | 地址与实例类型不匹配：新版个人版必须用 `crpi-xxx.<region>.personal.cr.aliyuncs.com`，不能用 `registry.<region>.aliyuncs.com`；也可能是用户名填了登录邮箱而非「账号全名」 |
| 证书签发失败 | 80 未放行 / DNS 未生效（`dig +short 域名`）/ 域名未备案 |
| 首次访问是 404，刷新才正常 | 镜像里是旧代码（缺 SPA 回落），重新部署 |
| 回答不是流式，一次性蹦出来 | Caddy 少了 `flush_interval -1`，或中间又加了一层缓冲代理 |
| 应用起不来，日志报 JWT | `ENV=prod` 但 `JWT_SECRET` 还是默认值 |
| 登录后立刻掉线 | `COOKIE_SECURE=true` 但当前是 http 访问 |
| 数据库认证失败 | 卷已初始化后改过 `POSTGRES_PASSWORD`，需在库内 `ALTER USER` |
| 内存吃紧 / OOM | 本方案单副本、单 uvicorn worker（并发限流是进程内信号量，**不能扩副本**）；2G 内存建议加 1G swap |

---

## 8. 已知边界

- **单副本**：`GLOBAL_CONCURRENCY` / 单用户串行是进程内信号量，水平扩副本会让限流失效。要扩就得把限流挪到 Redis。
- **文档/知识库**：`EMBED_BASE_URL` 默认指向家里 `100.64.0.10:7997`（Tailscale），当前代码尚未真正调用，不影响线上启动和聊天；接 RAG 时要么服务器加入 Tailscale，要么换成公网可达的推理服务。
- **建表**：应用启动时 `create_all` 只建缺失的表，**不会给已有表加列**。以后改 `models.py` 需要配 Alembic 迁移，或手动 `ALTER TABLE`。
- **数据目录**：`./data` 整体挂到容器 `/data`，`/opt/onefold/data/backup` 里的 sql 会被后台的存储统计算进去，所以备份目录独立放在 `/opt/onefold/backup`。
