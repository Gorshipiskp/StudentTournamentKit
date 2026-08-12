# STK verify - Foundation + Game + Production + People + Tournament Slice (TZ005 GATE)
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "== STK verify (TZ005 Tournament GATE) ==" -ForegroundColor Cyan
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
Write-Host "[1/7] artifacts (game + production + people + tournament)" -ForegroundColor Cyan
$required = @(
  "infra/game-server/CONTRACT.md",
  "tools/fake-cs2/fake_cs2/cli.py",
  "infra/game-server/plugins/STK.Bridge/STK.Bridge.csproj",
  "infra/game-server/plugins/STK.Bridge/README.md",
  "scripts/deploy-cs2.sh",
  "infra/game-server/README.md",
  "docs/OVERLAY-CONTRACT.md",
  "docs/WEBRTC-CONTRACT.md",
  "apps/director-agent/templates/scenes.json",
  "apps/director-agent/templates/README.md",
  "apps/director-agent/README.md",
  "apps/overlay/package.json",
  "apps/dashboard/package.json",
  "apps/judge/package.json",
  "apps/dashboard/src/lib/WizardNav.svelte",
  "apps/dashboard/src/lib/AdminPage.svelte",
  "apps/api/tests/test_multi_tournament_smoke.py",
  "workers/developer/notes/TZ003-OWNER-SMOKE.md",
  "workers/developer/notes/TZ004-OWNER-SMOKE.md",
  "workers/developer/notes/TZ005-OWNER-SMOKE.md",
  "workers/developer/notes/TZ005-PROMPT-RUNBOOK.md",
  "apps/director-agent/internal/infrastructure/webrtc/testdata/pattern.ivf",
  "apps/api/alembic/versions/0012_tournament_branding.py"
)
foreach ($rel in $required) {
  $p = Join-Path $Root $rel
  if (-not (Test-Path $p)) {
    throw "missing required artifact: $rel"
  }
}
Write-Host "OK artifacts"

Write-Host ""
Write-Host "[2/7] docker compose config (+ webrtc profile)" -ForegroundColor Cyan
$composeFile = "infra/platform/docker-compose.yml"
docker compose --env-file .env -f $composeFile config --quiet
if ($LASTEXITCODE -ne 0) {
  throw "compose config failed"
}
docker compose --env-file .env -f $composeFile --profile webrtc config --quiet
if ($LASTEXITCODE -ne 0) {
  throw "compose --profile webrtc config failed"
}
Write-Host "OK compose config (incl. coturn profile)"

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
Write-Host "[6/7] director-agent go test (+ fake-webrtc package)" -ForegroundColor Cyan
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
Write-Host "[7/7] alembic head present (0012 branding)" -ForegroundColor Cyan
$mig = Join-Path $Root "apps/api/alembic/versions/0012_tournament_branding.py"
if (-not (Test-Path $mig)) {
  throw "missing alembic 0012_tournament_branding"
}
$migInvite = Join-Path $Root "apps/api/alembic/versions/0008_invite_tokens.py"
if (-not (Test-Path $migInvite)) {
  throw "missing alembic 0008_invite_tokens"
}
Write-Host "OK migrations artifact"

Write-Host ""
Write-Host "VERIFY OK - TZ005 Tournament GATE (Fake match sufficient)" -ForegroundColor Green
Write-Host "live_cs2 / live_webrtc = blocked (optional; see TZ005-OWNER-SMOKE)" -ForegroundColor Yellow
Write-Host "Owner smoke: workers/developer/notes/TZ005-OWNER-SMOKE.md" -ForegroundColor Yellow
Write-Host "Next: TZ006 Broadcast Slice" -ForegroundColor Yellow
exit 0
