#!/usr/bin/env bash
# deploy-cs2.sh — install path for CS2 dedicated + Metamod + CSS + MatchZy + STK.Bridge
# Target: clean Ubuntu 22.04/24.04 VPS. Does NOT run without explicit confirmation.
#
# Usage:
#   ./scripts/deploy-cs2.sh --dry-run          # print plan only (safe)
#   ./scripts/deploy-cs2.sh --yes             # execute (requires root / sudo on VPS)
#
# Env (optional):
#   CS2_INSTALL_DIR=/opt/cs2
#   STK_REPO_DIR=/opt/BestCSTournaments
#   PLATFORM_URL=https://platform.example
#   CS2_WEBHOOK_SECRET=...
#   STK_MATCH_ID=m_...
#   STK_SERVER_ID=srv_...

set -euo pipefail

DRY_RUN=1
ASSUME_YES=0
CS2_INSTALL_DIR="${CS2_INSTALL_DIR:-/opt/cs2}"
STK_REPO_DIR="${STK_REPO_DIR:-}"
STEAMCMD_DIR="${STEAMCMD_DIR:-/opt/steamcmd}"

log() { printf '[deploy-cs2] %s\n' "$*"; }
run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "DRY-RUN: $*"
  else
    log "+ $*"
    eval "$@"
  fi
}

usage() {
  sed -n '1,20p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --yes|--execute) DRY_RUN=0; ASSUME_YES=1; shift ;;
    -h|--help) usage ;;
    *) log "unknown arg: $1"; usage ;;
  esac
done

if [[ "$DRY_RUN" -eq 0 && "$ASSUME_YES" -ne 1 ]]; then
  log "Refusing to execute without --yes"
  exit 1
fi

log "=== CS2 deploy plan ==="
log "install_dir=$CS2_INSTALL_DIR steamcmd=$STEAMCMD_DIR dry_run=$DRY_RUN"
log ""
log "Steps (operator checklist):"
log "  1) apt: curl, lib32gcc-s1, gdb, net-tools, ufw"
log "  2) Install SteamCMD → $STEAMCMD_DIR"
log "  3) SteamCMD: app_update 730 validate (CS2 dedicated)"
log "  4) Install Metamod:Source for CS2 (see alliedmods / CSS docs)"
log "  5) Install CounterStrikeSharp into game/csgo/addons/counterstrikesharp"
log "  6) Install MatchZy plugin (do NOT fork — ADR-010/023)"
log "  7) Build/copy STK.Bridge → addons/counterstrikesharp/plugins/STK.Bridge/"
log "  8) Write Bridge config.json (PlatformUrl, WebhookSecret, MatchId, ServerId, CommandListenPort)"
log "  9) Firewall: UDP/TCP 27015 (game), UDP 27020 (GOTV), outbound 443; open CommandListenPort to Platform only"
log " 10) Register server on Platform: POST /api/v1/game-servers + assign-server"
log " 11) GOTV: tv_enable 1, tv_autorecord 1 — demo path documented; durable copy via Platform after match (ADR-034)"
log ""

# --- executable dry-run / real stubs (idempotent mkdir only in dry-run prints) ---
run "mkdir -p '$CS2_INSTALL_DIR' '$STEAMCMD_DIR'"

if [[ "$DRY_RUN" -eq 1 ]]; then
  log "SteamCMD (example):"
  log "  curl -fsSL https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz | tar -xz -C $STEAMCMD_DIR"
  log "  $STEAMCMD_DIR/steamcmd.sh +force_install_dir $CS2_INSTALL_DIR +login anonymous +app_update 730 validate +quit"
  log ""
  log "Metamod / CSS / MatchZy: follow current upstream docs (versions change — recon on VPS)."
  log "  CSS: https://docs.cssharp.dev/"
  log "  MatchZy: https://github.com/shobhit-pathak/MatchZy"
  log "  Bridge: \$REPO/infra/game-server/plugins/STK.Bridge (dotnet build — see plugin README)"
  log ""
  log "Register hint:"
  log "  curl -X POST \$PLATFORM_URL/api/v1/game-servers -H 'Content-Type: application/json' \\"
  log "    -d '{\"server_id\":\"\$STK_SERVER_ID\",\"endpoint_url\":\"http://<cs2-public-ip>:27099\",\"webhook_secret\":\"\$CS2_WEBHOOK_SECRET\"}'"
  log "  curl -X POST \$PLATFORM_URL/api/v1/matches/<match_id>/assign-server -d '{\"server_id\":\"\$STK_SERVER_ID\"}'"
  log ""
  log "DRY-RUN complete — no packages installed. Re-run with --yes on the CS2 VPS as root when ready."
  exit 0
fi

# --- execute mode: minimal scaffolding only (full Steam download is long; document remaining) ---
if [[ "$(id -u)" -ne 0 ]]; then
  log "execute mode expects root (sudo)"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y curl ca-certificates lib32gcc-s1 tar

if [[ ! -x "$STEAMCMD_DIR/steamcmd.sh" ]]; then
  mkdir -p "$STEAMCMD_DIR"
  curl -fsSL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" \
    | tar -xz -C "$STEAMCMD_DIR"
fi

log "SteamCMD ready at $STEAMCMD_DIR"
log "Next (manual / long): app_update 730, Metamod, CSS, MatchZy, Bridge publish."
log "See infra/game-server/README.md for full operator runbook."
exit 0
