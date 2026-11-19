#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PREV=$(cat .current_tag 2>/dev/null || echo "")
# 由 CI 调用时 TAG/ONEFOLD_IMAGE 由 workflow 传入；手工执行时从 .current_tag 与 .env 兜底，
# 否则 compose 会退化成 onefold:latest 而报 No such image
export TAG=${TAG:-$(cat .current_tag 2>/dev/null || echo latest)}
export ONEFOLD_IMAGE=${ONEFOLD_IMAGE:-$(grep -E '^ONEFOLD_IMAGE=' .env 2>/dev/null | cut -d= -f2-)}
if [ -n "${TAG:-}" ]; then
  echo "$TAG" > .current_tag
fi

mkdir -p data/backup data/uploads
# 容器内以 appuser(uid 10001) 运行，挂载进来的宿主机目录必须是同一属主，
# 否则启动时 documents.py 创建 /data/uploads 会 PermissionError
chown -R 10001:10001 data 2>/dev/null || true
# 备份 PostgreSQL；db 容器未启动时跳过
docker compose exec -T db pg_dump -U onefold onefold > "data/backup/onefold-$(date +%Y%m%d%H%M%S).sql" 2>/dev/null || true

docker compose pull || true
docker compose up -d

for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/healthz >/dev/null; then
    docker image prune -f >/dev/null 2>&1 || true
    echo "deploy ok: ${TAG:-latest}"
    exit 0
  fi
  sleep 2
done

echo "healthcheck failed"
if [ -n "$PREV" ]; then
  echo "rollback to $PREV"
  TAG="$PREV" docker compose up -d
  # 回滚后要再探一次，并把锚点写回去；否则下一次手工 ./deploy.sh 会读到失败的 tag
  if curl -fsS --retry 10 --retry-delay 2 --retry-connrefused http://127.0.0.1:8000/healthz >/dev/null; then
    echo "$PREV" > .current_tag
    echo "rollback ok: $PREV"
  else
    echo "rollback failed: 需要人工介入"
  fi
fi
exit 1
