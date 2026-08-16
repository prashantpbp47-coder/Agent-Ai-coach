#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/partnershub-ai}"
BRANCH="${BRANCH:-main}"

cd "$APP_DIR"

git fetch origin "$BRANCH"
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

# Require a real environment file outside Git.
test -f .env.production || { echo "Missing $APP_DIR/.env.production" >&2; exit 1; }

# Validate the Compose model before changing running services.
docker compose --env-file .env.production -f docker-compose.production.yml config >/dev/null

docker compose --env-file .env.production -f docker-compose.production.yml build --pull
docker compose --env-file .env.production -f docker-compose.production.yml up -d

echo "Waiting for application health..."
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/api/p19/health >/dev/null 2>&1; then
    echo "PartnersHub AI deployment: HEALTHY"
    exit 0
  fi
  sleep 2
done

echo "PartnersHub AI deployment: HEALTH CHECK FAILED" >&2
docker compose --env-file .env.production -f docker-compose.production.yml ps >&2 || true
docker compose --env-file .env.production -f docker-compose.production.yml logs --tail=120 app >&2 || true
exit 1
