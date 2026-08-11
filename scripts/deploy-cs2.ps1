# deploy-cs2.ps1 — Windows helper: dry-run plan for CS2 VPS deploy (bash script is canonical on Linux VPS)
# Usage:
#   .\scripts\deploy-cs2.ps1
#   .\scripts\deploy-cs2.ps1 -ExecuteHint   # prints how to run bash on VPS

param(
  [switch]$ExecuteHint
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Bash = Join-Path $PSScriptRoot "deploy-cs2.sh"

Write-Host "== deploy-cs2 (Windows helper) ==" -ForegroundColor Cyan
Write-Host "Canonical installer: scripts/deploy-cs2.sh (Ubuntu VPS)"
Write-Host "Repo root: $Root"
Write-Host ""
Write-Host "Dry-run plan (no SSH / no install on this machine):" -ForegroundColor Yellow

if (Get-Command bash -ErrorAction SilentlyContinue) {
  try {
    & bash $Bash --dry-run
    if ($LASTEXITCODE -ne 0) { throw "bash dry-run failed" }
  } catch {
    Write-Host "bash unavailable or failed — printing summary:" -ForegroundColor Yellow
    Write-Host @"

  1) SteamCMD + CS2 DS (app 730) on Ubuntu VPS
  2) Metamod → CounterStrikeSharp → MatchZy (no fork)
  3) Build/copy STK.Bridge to plugins/STK.Bridge
  4) Firewall 27015/27020 + Bridge command port to Platform
  5) POST /api/v1/game-servers + assign-server
  6) After match: durable demo via Platform data/demos (ADR-034)

Full text: infra/game-server/README.md
  Canonical: scripts/deploy-cs2.sh --dry-run
"@
  }
} else {
  Write-Host @"
[deploy-cs2] bash not in PATH — printing summary:

  1) SteamCMD + CS2 DS (app 730) on Ubuntu VPS
  2) Metamod → CounterStrikeSharp → MatchZy (no fork)
  3) Build/copy STK.Bridge to plugins/STK.Bridge
  4) Firewall 27015/27020 + Bridge command port to Platform
  5) POST /api/v1/game-servers + assign-server
  6) After match: durable demo via Platform data/demos (ADR-034)

Full text: infra/game-server/README.md
"@
}

if ($ExecuteHint) {
  Write-Host ""
  Write-Host "On CS2 VPS:" -ForegroundColor Green
  Write-Host "  sudo bash scripts/deploy-cs2.sh --dry-run"
  Write-Host "  sudo bash scripts/deploy-cs2.sh --yes   # after review"
}
