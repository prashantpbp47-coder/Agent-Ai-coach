#!/bin/sh
set -eu

: "${DATABASE_URL:?DATABASE_URL must be set}"

echo "[deploy] upgrading database"
alembic upgrade head

echo "[deploy] starting gunicorn"
exec gunicorn --config deploy/gunicorn.conf.py wsgi:app
