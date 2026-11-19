#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PREV=$(cat .current_tag 2>/dev/null || echo "")
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
fi
exit 1
