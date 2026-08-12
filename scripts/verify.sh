#!/usr/bin/env bash
# Local verify — twin of verify.ps1 (TZ004 People GATE)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== STK verify (TZ004 People GATE) =="
echo "root: $ROOT"

if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    echo "No .env — copying .env.example"
    cp .env.example .env
  else
    echo "Missing .env / .env.example" >&2
    exit 1
  fi
fi

echo
echo "[1/7] artifacts"
for f in \
  infra/game-server/CONTRACT.md \
  tools/fake-cs2/fake_cs2/cli.py \
  docs/OVERLAY-CONTRACT.md \
  docs/WEBRTC-CONTRACT.md \
  apps/director-agent/README.md \
  apps/overlay/package.json \
  apps/dashboard/package.json \
  apps/judge/package.json \
  workers/developer/notes/TZ004-OWNER-SMOKE.md \
  apps/director-agent/internal/infrastructure/webrtc/testdata/pattern.ivf \
  apps/api/alembic/versions/0008_invite_tokens.py
do
  [[ -f "$f" ]] || { echo "missing $f" >&2; exit 1; }
done
echo "OK artifacts"

echo
echo "[2/7] docker compose config (+ webrtc)"
docker compose --env-file .env -f infra/platform/docker-compose.yml config --quiet
docker compose --env-file .env -f infra/platform/docker-compose.yml --profile webrtc config --quiet
echo "OK compose config"

echo
echo "[3/7] pytest apps/api"
cd apps/api
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -e ".[dev]"
fi
export MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
export MYSQL_PORT="${MYSQL_PORT:-3307}"
export MYSQL_USER="${MYSQL_USER:-stk}"
export MYSQL_PASSWORD="${MYSQL_PASSWORD:-changeme_stk_dev}"
export MYSQL_DATABASE="${MYSQL_DATABASE:-stk}"
export MYSQL_SSL="${MYSQL_SSL:-}"
export STK_SESSION_SECRET="${STK_SESSION_SECRET:-dev_session_secret_change_me}"
export STK_AGENT_TOKEN="${STK_AGENT_TOKEN:-dev_agent_token_change_me}"
export TURN_SECRET="${TURN_SECRET:-dev_turn_secret_change_me}"
.venv/bin/python -m pytest -q
cd "$ROOT"
echo "OK pytest"

echo
echo "[4/7] fake-cs2 self-test"
cd tools/fake-cs2
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -e ".[dev]"
fi
.venv/bin/python -m fake_cs2 self-test
.venv/bin/python -m pytest -q
cd "$ROOT"
echo "OK fake-cs2"

echo
echo "[5/7] overlay + dashboard + judge build"
npm_build() {
  local dir="$1"
  cd "$ROOT/$dir"
  if [[ ! -d node_modules ]]; then
    npm install --no-fund
  fi
  npm run build
  if grep -q '"test"' package.json 2>/dev/null; then
    npm test || true
  fi
  cd "$ROOT"
}
# Prefer failing on test if script exists properly
npm_build_strict() {
  local dir="$1"
  cd "$ROOT/$dir"
  if [[ ! -d node_modules ]]; then
    npm install --no-fund
  fi
  npm run build
  if node -e "const p=require('./package.json'); process.exit(p.scripts&&p.scripts.test?0:1)"; then
    npm test
  fi
  cd "$ROOT"
}
npm_build_strict apps/overlay
npm_build_strict apps/dashboard
npm_build_strict apps/judge
echo "OK frontend builds"

echo
echo "[6/7] director-agent go test"
command -v go >/dev/null || { echo "go not found" >&2; exit 1; }
cd apps/director-agent
go test ./...
go build -o stk-director-agent ./cmd/agent
cd "$ROOT"
echo "OK director-agent"

echo
echo "[7/7] OK migrations artifact"
echo
echo "VERIFY OK — TZ004 People GATE (fake-webrtc sufficient)"
echo "live_webrtc = blocked (OBS Virtual Cam optional)"
