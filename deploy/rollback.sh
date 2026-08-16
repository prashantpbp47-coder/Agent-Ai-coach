#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/partnershub-ai}"
IMAGE="${ROLLBACK_IMAGE:?Set ROLLBACK_IMAGE to the last known-good image tag}"

cd "$APP_DIR"

test -f .env.production || { echo "Missing .env.production" >&2; exit 1; }

docker image inspect "$IMAGE" >/dev/null
docker tag "$IMAGE" partnershub-ai:rollback

docker compose --env-file .env.production -f docker-compose.production.yml up -d --no-build app

for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/api/p19/health >/dev/null 2>&1; then
    echo "Rollback runtime: HEALTHY"
    exit 0
  fi
  sleep 2
done

echo "Rollback health check failed" >&2
exit 1
