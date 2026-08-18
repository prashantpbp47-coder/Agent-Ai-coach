#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Render Free web services do not provide Dashboard Shell or pre-deploy commands.
# Run Alembic here so every successful build can advance the connected database
# to the current migration head without requiring a paid instance.
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is required for Render database migration."
  exit 1
fi

python -m alembic upgrade head
python -m alembic current
python -m alembic check

echo "Render build + database migration completed successfully."
