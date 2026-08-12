#!/usr/bin/env bash
# STK dev stack — remote MySQL + API on host + Vite (overlay/dashboard)
# Usage: ./scripts/dev-remote.sh [match_id]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MATCH_ID="${1:-m_dev}"
API_ONLY="${API_ONLY:-0}"
SKIP_MIGRATE="${SKIP_MIGRATE:-0}"
ALLOW_LOCAL_DB="${ALLOW_LOCAL_DB:-0}"

ENV_FILE="$ROOT/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$ROOT/.env.example" ]]; then
    cp "$ROOT/.env.example" "$ENV_FILE"
    echo "Copied .env.example -> .env"
  else
    echo "Missing .env" >&2
    exit 1
  fi
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ -z "${MYSQL_HOST:-}" ]]; then
  echo "MYSQL_HOST is empty in .env" >&2
  exit 1
fi
if [[ "$MYSQL_HOST" == "mysql" ]]; then
  echo "MYSQL_HOST=mysql is for Docker Compose. Set remote host in .env + MYSQL_SSL=1." >&2
  exit 1
fi
if [[ "$ALLOW_LOCAL_DB" != "1" && ( "$MYSQL_HOST" == "127.0.0.1" || "$MYSQL_HOST" == "localhost" ) ]]; then
  echo "MYSQL_HOST=$MYSQL_HOST looks local. Set ALLOW_LOCAL_DB=1 to override." >&2
  exit 1
fi

API_PORT="${API_PORT:-8000}"
VENV_PY="$ROOT/apps/api/.venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  echo "Creating apps/api/.venv ..."
  (cd "$ROOT/apps/api" && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]")
fi

if [[ "$SKIP_MIGRATE" != "1" ]]; then
  echo "Alembic upgrade (remote DB) ..."
  (cd "$ROOT/apps/api" && "$VENV_PY" -m alembic upgrade head)
fi

PIDS=()
cleanup() {
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

echo "== STK dev-remote =="
echo "MySQL: ${MYSQL_HOST}:${MYSQL_PORT:-3306}/${MYSQL_DATABASE:-stk}"

(cd "$ROOT/apps/api" && "$VENV_PY" -m uvicorn app.main:app --host 127.0.0.1 --port "$API_PORT" --reload) &
PIDS+=($!)
echo "API pid ${PIDS[-1]} :$API_PORT"

if [[ "$API_ONLY" != "1" ]]; then
  for app in overlay dashboard; do
    dir="$ROOT/apps/$app"
    if [[ ! -d "$dir/node_modules" ]]; then
      echo "npm install in $app ..."
      (cd "$dir" && npm install)
    fi
    (cd "$dir" && npm run dev) &
    PIDS+=($!)
    echo "$app pid ${PIDS[-1]}"
  done
fi

echo ""
echo "  health   http://127.0.0.1:${API_PORT}/health"
echo "  overlay  http://127.0.0.1:5173/overlay/${MATCH_ID}"
echo "  director http://127.0.0.1:5174/director/${MATCH_ID}"
echo ""
echo "Ctrl+C stops all background processes."

wait
