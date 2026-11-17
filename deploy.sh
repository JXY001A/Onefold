#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PREV=$(cat .current_tag 2>/dev/null || echo "")
if [ -n "${TAG:-}" ]; then
  echo "$TAG" > .current_tag
fi

mkdir -p data/backup
cp -f data/onefold.db "data/backup/onefold-$(date +%Y%m%d%H%M%S).db" 2>/dev/null || true

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
