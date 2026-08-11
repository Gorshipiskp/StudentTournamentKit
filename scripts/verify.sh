#!/usr/bin/env bash
# Local verify — Foundation + Game Slice GATE (twin of verify.ps1)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== STK verify (Game Slice GATE) =="
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
echo "[1/4] artifacts"
for f in \
  infra/game-server/CONTRACT.md \
  tools/fake-cs2/fake_cs2/cli.py \
  infra/game-server/plugins/STK.Bridge/STK.Bridge.csproj \
  scripts/deploy-cs2.sh \
  infra/game-server/README.md
do
  [[ -f "$f" ]] || { echo "missing $f" >&2; exit 1; }
done
echo "OK artifacts"

echo
echo "[2/4] docker compose config"
docker compose --env-file .env -f infra/platform/docker-compose.yml config --quiet
echo "OK compose config"

echo
echo "[3/4] pytest apps/api"
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
.venv/bin/python -m pytest -q
cd "$ROOT"
echo "OK pytest"

echo
echo "[4/4] fake-cs2 self-test"
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
echo "VERIFY OK — TZ002 primary GATE (Fake)"
echo "live_smoke=blocked (no VPS / @owner SSH)"
