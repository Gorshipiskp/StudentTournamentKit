# STK verify - Production Ready (TZ010; Fake CI - live OBS/CS2/WHIP not required)
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "== STK verify (TZ010 Production Ready - Fake CI; live OBS/CS2/WHIP not required) ==" -ForegroundColor Cyan
Write-Host ("root: {0}" -f $Root)

$EnvFile = Join-Path $Root ".env"
$EnvExample = Join-Path $Root ".env.example"
if (-not (Test-Path $EnvFile)) {
  if (Test-Path $EnvExample) {
    Write-Host "No .env - copying .env.example (dev placeholders)" -ForegroundColor Yellow
    Copy-Item $EnvExample $EnvFile
  }
  else {
    throw ".env and .env.example missing"
  }
}

Write-Host ""
Write-Host "[1/7] artifacts (TZ010 Production Ready + prior)" -ForegroundColor Cyan
$required = @(
  "docs/PRODUCTION-RUNBOOK.md",
  "docs/PRODUCTION-RECOVERY.md",
  "docs/UPDATE.md",
  "workers/developer/notes/TZ010-PROMPT-RUNBOOK.md",
  "workers/developer/notes/TZ010-OWNER-SMOKE.md",
  "workers/developer/notes/TZ010-RECON.md",
  "tasks/010_PRODUCTION-READY.md",
  "infra/game-server/CONTRACT.md",
  "infra/game-server/LOCAL-CS2-DS.md",
  "tools/fake-cs2/fake_cs2/cli.py",
  "infra/game-server/plugins/STK.Bridge/STK.Bridge.csproj",
  "infra/game-server/plugins/STK.Bridge/GameScoreReader.cs",
  "infra/mediamtx/mediamtx.yml",
  "infra/mediamtx/README.md",
  "infra/mediamtx/spike/whep.html",
  "docs/OVERLAY-CONTRACT.md",
  "docs/WEBRTC-CONTRACT.md",
  "docs/BROADCAST-DELAY.md",
  "docs/BROADCAST-HEALTH.md",
  "docs/ALPHA-RUNBOOK.md",
  "docs/ALPHA-LIVE-TRACKS.md",
  "docs/alpha/organizer.md",
  "docs/alpha/director.md",
  "docs/alpha/judge.md",
  "docs/alpha/POST-MORTEM-TEMPLATE.md",
  "scripts/alpha-dry-run.ps1",
  "apps/director-agent/templates/scenes.json",
  "apps/director-agent/templates/README.md",
  "apps/director-agent/internal/infrastructure/webrtc/live_track.go",
  "apps/director-agent/internal/infrastructure/webrtc/fake_track.go",
  "apps/director-agent/internal/infrastructure/webrtc/README.md",
  "apps/overlay/src/lib/scenes/WaitingScene.svelte",
  "apps/overlay/src/lib/scenes/WinnerScene.svelte",
  "apps/overlay/src/lib/whepClient.ts",
  "apps/overlay/src/lib/WatchPage.svelte",
  "apps/dashboard/src/lib/DirectorPage.svelte",
  "apps/dashboard/src/lib/MatchOps.svelte",
  "apps/api/app/application/commands/get_match_health.py",
  "apps/api/app/application/commands/write_audit.py",
  "apps/api/app/application/commands/start_match.py",
  "apps/api/app/presentation/http/routers/whip.py",
  "apps/api/app/infrastructure/security/mediamtx_credentials.py",
  "apps/api/tests/test_match_health_unit.py",
  "apps/api/tests/test_audit_unit.py",
  "apps/api/tests/test_match_ops_unit.py",
  "apps/api/tests/test_mediamtx_credentials_unit.py",
  "apps/api/tests/test_failures_a_e.py",
  "workers/developer/notes/TZ006-OWNER-SMOKE.md",
  "workers/developer/notes/TZ007-OWNER-SMOKE.md",
  "workers/developer/notes/TZ007-PROMPT-RUNBOOK.md",
  "workers/developer/notes/TZ008-PROMPT-RUNBOOK.md",
  "workers/developer/notes/TZ008-OWNER-SMOKE.md",
  "workers/developer/notes/TZ009-PROMPT-RUNBOOK.md",
  "workers/developer/notes/TZ009-OWNER-SMOKE.md",
  "workers/developer/notes/TZ009-RECON.md",
  "workers/developer/notes/TZ011-PROMPT-RUNBOOK.md",
  "workers/developer/notes/TZ011-OWNER-SMOKE.md",
  "workers/developer/notes/TZ011-SPIKE.md",
  "tasks/008_LIVE-WEBRTC.md",
  "tasks/009_LIVE-CS2-LOCAL.md",
  "tasks/011_OBS-WHIP.md",
  "apps/api/alembic/versions/0012_tournament_branding.py",
  "apps/api/alembic/versions/0013_match_audit_log.py"
)
foreach ($rel in $required) {
  $p = Join-Path $Root $rel
  if (-not (Test-Path $p)) {
    throw "missing required artifact: $rel"
  }
}
Write-Host "OK artifacts"

Write-Host ""
Write-Host "[2/7] docker compose config (webrtc and whip profiles)" -ForegroundColor Cyan
$composeFile = "infra/platform/docker-compose.yml"
docker compose --env-file .env -f $composeFile config --quiet
if ($LASTEXITCODE -ne 0) {
  throw "compose config failed"
}
docker compose --env-file .env -f $composeFile --profile webrtc config --quiet
if ($LASTEXITCODE -ne 0) {
  throw "compose --profile webrtc config failed"
}
docker compose --env-file .env -f $composeFile --profile whip config --quiet
if ($LASTEXITCODE -ne 0) {
  throw "compose --profile whip config failed"
}
Write-Host "OK compose config (coturn + mediamtx profiles; containers need not be up)"

Write-Host ""
Write-Host "[3/7] pytest apps/api" -ForegroundColor Cyan
$apiDir = Join-Path $Root "apps/api"
$venvPython = Join-Path $apiDir ".venv/Scripts/python.exe"
if (-not (Test-Path $venvPython)) {
  Write-Host "Creating apps/api/.venv and installing deps..." -ForegroundColor Yellow
  Push-Location $apiDir
  try {
    python -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) {
      throw "pip install failed"
    }
  }
  finally {
    Pop-Location
  }
}

if (-not $env:MYSQL_HOST) { $env:MYSQL_HOST = "127.0.0.1" }
if (-not $env:MYSQL_PORT) { $env:MYSQL_PORT = "3307" }
if (-not $env:MYSQL_USER) { $env:MYSQL_USER = "stk" }
if (-not $env:MYSQL_PASSWORD) { $env:MYSQL_PASSWORD = "changeme_stk_dev" }
if (-not $env:MYSQL_DATABASE) { $env:MYSQL_DATABASE = "stk" }
if (-not $env:STK_SESSION_SECRET) { $env:STK_SESSION_SECRET = "dev_session_secret_change_me" }
if (-not $env:STK_AGENT_TOKEN) { $env:STK_AGENT_TOKEN = "dev_agent_token_change_me" }
if (-not $env:TURN_SECRET) { $env:TURN_SECRET = "dev_turn_secret_change_me" }
if (-not $env:STK_ORGANIZER_USERNAME) { $env:STK_ORGANIZER_USERNAME = "organizer" }
if (-not $env:STK_ORGANIZER_PASSWORD) { $env:STK_ORGANIZER_PASSWORD = "changeme_organizer" }
$env:MYSQL_SSL = ""

Push-Location $apiDir
try {
  & $venvPython -m pytest -q
  if ($LASTEXITCODE -ne 0) {
    throw "pytest failed"
  }
}
finally {
  Pop-Location
}
Write-Host "OK pytest"

Write-Host ""
Write-Host "[4/7] fake-cs2 self-test" -ForegroundColor Cyan
$fakeDir = Join-Path $Root "tools/fake-cs2"
$fakePy = Join-Path $fakeDir ".venv/Scripts/python.exe"
if (-not (Test-Path $fakePy)) {
  Write-Host "Creating tools/fake-cs2/.venv..." -ForegroundColor Yellow
  Push-Location $fakeDir
  try {
    python -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) {
      throw "fake-cs2 pip install failed"
    }
  }
  finally {
    Pop-Location
  }
}
Push-Location $fakeDir
try {
  & $fakePy -m fake_cs2 self-test
  if ($LASTEXITCODE -ne 0) {
    throw "fake-cs2 self-test failed"
  }
  & $fakePy -m pytest -q
  if ($LASTEXITCODE -ne 0) {
    throw "fake-cs2 pytest failed"
  }
}
finally {
  Pop-Location
}
Write-Host "OK fake-cs2"

Write-Host ""
Write-Host "[5/7] overlay + dashboard + judge build" -ForegroundColor Cyan
function Invoke-NpmBuild([string]$AppRel) {
  $appDir = Join-Path $Root $AppRel
  Push-Location $appDir
  try {
    if (-not (Test-Path "node_modules")) {
      Write-Host ("npm install ({0})..." -f $AppRel) -ForegroundColor Yellow
      npm install --no-fund
      if ($LASTEXITCODE -ne 0) { throw "npm install failed: $AppRel" }
    }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build failed: $AppRel" }
    if (Test-Path "package.json") {
      $pkg = Get-Content "package.json" -Raw | ConvertFrom-Json
      if ($pkg.scripts.test) {
        npm test
        if ($LASTEXITCODE -ne 0) { throw "npm test failed: $AppRel" }
      }
    }
  }
  finally {
    Pop-Location
  }
}
Invoke-NpmBuild "apps/overlay"
Invoke-NpmBuild "apps/dashboard"
Invoke-NpmBuild "apps/judge"
Write-Host "OK frontend builds"

Write-Host ""
Write-Host "[6/7] director-agent go test (+ fake-webrtc + live_track unit, no OBS)" -ForegroundColor Cyan
$goCmd = Get-Command go -ErrorAction SilentlyContinue
if (-not $goCmd) {
  $goExe = "C:\Program Files\Go\bin\go.exe"
  if (Test-Path $goExe) {
    $env:Path = "C:\Program Files\Go\bin;" + $env:Path
    $goCmd = Get-Command go -ErrorAction SilentlyContinue
  }
}
if (-not $goCmd) {
  throw "go not found in PATH (install Go 1.22+ for Agent GATE)"
}
$agentDir = Join-Path $Root "apps/director-agent"
Push-Location $agentDir
try {
  go test ./...
  if ($LASTEXITCODE -ne 0) {
    throw "director-agent go test failed"
  }
  go build -o stk-director-agent.exe ./cmd/agent
  if ($LASTEXITCODE -ne 0) {
    throw "director-agent go build failed"
  }
}
finally {
  Pop-Location
}
Write-Host "OK director-agent"

Write-Host ""
Write-Host "[7/7] alembic artifacts (0013 audit + 0012 branding)" -ForegroundColor Cyan
$mig = Join-Path $Root "apps/api/alembic/versions/0013_match_audit_log.py"
if (-not (Test-Path $mig)) {
  throw "missing alembic 0013_match_audit_log"
}
$migBrand = Join-Path $Root "apps/api/alembic/versions/0012_tournament_branding.py"
if (-not (Test-Path $migBrand)) {
  throw "missing alembic 0012_tournament_branding"
}
Write-Host "OK migrations artifact"

Write-Host ""
Write-Host "VERIFY OK - TZ010 Production Ready (Fake CI; live OBS/CS2/WHIP not required)" -ForegroundColor Green
Write-Host "production_ready = gate_ready; @owner: TZ010-OWNER-SMOKE.md -> production_ready=done" -ForegroundColor Yellow
Write-Host "Also open: TZ011 live_whip / TZ009 live_cs2_local; TL: Twitch or BestTvGU" -ForegroundColor Yellow
exit 0
