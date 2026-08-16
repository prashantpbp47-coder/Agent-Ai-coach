#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

curl --fail --silent --show-error --max-time 10 "$BASE_URL/api/p19/health" >/dev/null
printf 'Application health: PASS\n'

curl --fail --silent --show-error --max-time 10 "$BASE_URL/api/p20/whatsapp/health" >/dev/null
printf 'P20 WhatsApp boundary health: PASS\n'
