#!/usr/bin/env bash
# ============================================================================
# deploy.sh —— Onefold 部署脚本
#
# 用法：
#   CI 调用：  TAG=<commit-sha> ONEFOLD_IMAGE=<仓库地址>/onefold ./deploy.sh
#   手工执行：./deploy.sh            （TAG 与镜像地址自动兜底，见下方）
#
# 流程：备份数据库 → 拉镜像 → 重建容器 → 探活 → 成功清理 / 失败回滚
# ============================================================================

# 严格模式，三个选项各行其职：
#   -e          任意命令返回非 0 就立即退出（避免错误被忽略后继续跑）
#   -u          引用未定义的变量直接报错（防止 $TYPO 静默变成空串）
#   -o pipefail 管道中任一环节失败，整条管道就算失败（默认只看最后一个命令）
# 正因如此，下面凡是「允许失败」的命令都显式加了 `|| true`。
set -euo pipefail

# 切换到脚本自身所在的目录（即 /opt/onefold）。
# 不管从哪个路径调用 ./deploy.sh，后续的相对路径（.current_tag、.env、data/）
# 都能正确定位。
cd "$(dirname "$0")"

# ---------------------------------------------------------------------------
# 1. 确定本次要部署的版本
# ---------------------------------------------------------------------------
# 记录「部署前正在运行的版本」，一旦新版本探活失败，就回滚到这里。
# 文件不存在时用空串兜底，表示这是首次部署、没有可回滚的版本。
PREV=$(cat .current_tag 2>/dev/null || echo "")

# 两个变量决定 compose 去拉哪个镜像：
#   TAG            镜像的 tag（就是 commit sha）
#   ONEFOLD_IMAGE  镜像仓库地址（compose 里写作 ${ONEFOLD_IMAGE:-onefold}）
#
# CI 调用时会显式传入这两个值；手工执行时没有传，则按下面的顺序兜底：
#   TAG            ← .current_tag（上次部署的版本）
#   ONEFOLD_IMAGE  ← .env 里配置的地址
# 不兜底的话，compose 会退化成默认值 onefold:latest，导致报 No such image。
export TAG=${TAG:-$(cat .current_tag 2>/dev/null || echo latest)}
export ONEFOLD_IMAGE=${ONEFOLD_IMAGE:-$(grep -E '^ONEFOLD_IMAGE=' .env 2>/dev/null | cut -d= -f2-)}

# 把本版本立即写入锚点文件。
# 为什么要提前写而不是等成功后再写：探活失败时脚本会 exit 1，若此时才写就来不及了。
# 提前写的副作用由后面的回滚分支负责修正（回滚成功会把旧版本号写回去）。
if [ -n "${TAG:-}" ]; then
  echo "$TAG" > .current_tag
fi

# ---------------------------------------------------------------------------
# 2. 准备数据目录并修正属主
# ---------------------------------------------------------------------------
mkdir -p data/backup data/uploads

# 容器内进程以 appuser 运行，UID 是 10001（见 Dockerfile 的 useradd）。
# 而 bind 挂载进来的 ./data 默认属主是 root，容器内写不进去，启动时会报：
#   PermissionError: [Errno 13] Permission denied: '/data/uploads'
# 所以每次部署都对齐一次属主。失败不阻断（例如在非 root 环境下跳过）。
chown -R 10001:10001 data 2>/dev/null || true

# ---------------------------------------------------------------------------
# 3. 备份数据库（在替换容器之前做，保证备份的是运行中的旧数据）
# ---------------------------------------------------------------------------
# -T 关闭伪终端分配，否则在非交互环境（CI）下 pg_dump 会失败。
# 输出重定向到 data/backup/onefold-<时间戳>.sql。
# 整体 || true：数据库还没起来（首次部署）或备份失败都不应阻止发布。
docker compose exec -T db pg_dump -U onefold onefold > "data/backup/onefold-$(date +%Y%m%d%H%M%S).sql" 2>/dev/null || true

# ---------------------------------------------------------------------------
# 4. 拉取镜像
# ---------------------------------------------------------------------------
# pull 允许失败：本地可能已有该镜像（重复部署），或 ACR 网络抖动。
# 即使拉不到，下面的 up 仍会用本地已有镜像启动。
docker compose pull || true

# ---------------------------------------------------------------------------
# 4.5 数据库迁移（必须在启动新 app 之前）
# ---------------------------------------------------------------------------
# 旧版本代码的 create_run 不会写 runs.turn_no；迁移把 turn_no 设为 NOT NULL
# 后，如果旧 app 还在跑，新 run 会插入失败。因此先停 app/worker。
# 迁移脚本已经随 Dockerfile 打进镜像。
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "==> migrate database"

  # 首次部署时 db 可能还没起；先确保容器存在并等待健康
  docker compose up -d db >/dev/null
  for _ in $(seq 1 30); do
    if docker compose exec -T db pg_isready -U onefold -d onefold >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  # 停旧 app / worker，避免迁移期间继续写旧结构
  docker compose stop app memory-worker >/dev/null 2>&1 || true

  # 先读当前 revision；命令失败和“空版本”要区分开
  if ! CURRENT_OUT=$(docker compose run --rm -T app alembic current 2>&1); then
    echo "$CURRENT_OUT"
    echo "==> alembic current failed"
    if [ -n "${PREV:-}" ]; then
      TAG="$PREV" docker compose up -d app memory-worker >/dev/null 2>&1 || true
    fi
    exit 1
  fi
  CURRENT=$(printf '%s\n' "$CURRENT_OUT" | grep -Eo '^[0-9a-f]{12}' | head -n 1 || true)

  # 已有库第一次接 Alembic：只 stamp 基线，不执行基线里的 CREATE TABLE
  if [ -z "$CURRENT" ]; then
    HAS_USERS=$(docker compose exec -T db psql -U onefold -d onefold -tAc \
      "select to_regclass('public.users') is not null;" | tr -d '[:space:]')
    if [ "$HAS_USERS" = "t" ]; then
      echo "==> legacy database: stamp baseline"
      docker compose run --rm -T app alembic stamp 317ce06e5e93
    fi
  fi

  if ! docker compose run --rm -T app alembic upgrade head; then
    echo "==> database migration failed"
    # 迁移失败时尽量把旧版本拉回来；数据库结构由 PostgreSQL 事务回滚兜底
    if [ -n "${PREV:-}" ]; then
      TAG="$PREV" docker compose up -d app memory-worker >/dev/null 2>&1 || true
    fi
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# 5. 重建容器
# ---------------------------------------------------------------------------
# 按 compose 配置创建/替换容器。
# -d 后台运行；配置未变化的服务（如 db、caddy）会被跳过，不会重启。
# 这一步不写 || true —— 容器起不来就必须中断，继续探活没有意义。
docker compose up -d

# ---------------------------------------------------------------------------
# 6. 探活：最多等待 60 秒（30 次 × 2 秒）
# ---------------------------------------------------------------------------
# 探测的是 127.0.0.1:8000 而不是公网域名：绕过 Caddy，直接验证应用本身。
# curl 的 -f 让 HTTP 4xx/5xx 也返回非 0，-sS 静默但保留错误输出。
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/healthz >/dev/null; then
    # 探活通过：清理无 tag 的悬空镜像（旧版本有 tag，不会被删）。
    docker image prune -f >/dev/null 2>&1 || true
    echo "deploy ok: ${TAG:-latest}"
    exit 0
  fi
  sleep 2
done

# ---------------------------------------------------------------------------
# 7. 失败回滚
# ---------------------------------------------------------------------------
echo "healthcheck failed"
if [ -n "$PREV" ]; then
  echo "rollback to $PREV"
  # 用上一版的 TAG 重新 up -d，容器会被替换回旧镜像
  TAG="$PREV" docker compose up -d

  # 回滚后要再探一次，并把锚点写回去；否则下一次手工 ./deploy.sh 会读到失败的 tag
  # --retry-connrefused 让 curl 在容器还没开始监听端口时继续重试，而不是立刻失败
  if curl -fsS --retry 10 --retry-delay 2 --retry-connrefused http://127.0.0.1:8000/healthz >/dev/null; then
    echo "$PREV" > .current_tag
    echo "rollback ok: $PREV"
  else
    # 上一版也起不来，通常是外部依赖问题（数据库连不上、.env 写错、端口被占用）
    echo "rollback failed: 需要人工介入"
  fi
fi

# 无论回滚成功与否都以非 0 退出，让 CI 变红，提醒有人需要去看
exit 1
