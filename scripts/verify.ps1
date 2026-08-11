# STK verify — Foundation + Game Slice (TZ002 GATE)
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "== STK verify (Game Slice GATE) ==" -ForegroundColor Cyan
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
Write-Host "[1/4] artifacts (contract, fake, bridge, deploy)" -ForegroundColor Cyan
$required = @(
  "infra/game-server/CONTRACT.md",
  "tools/fake-cs2/fake_cs2/cli.py",
  "infra/game-server/plugins/STK.Bridge/STK.Bridge.csproj",
  "infra/game-server/plugins/STK.Bridge/README.md",
  "scripts/deploy-cs2.sh",
  "infra/game-server/README.md"
)
foreach ($rel in $required) {
  $p = Join-Path $Root $rel
  if (-not (Test-Path $p)) {
    throw "missing required artifact: $rel"
  }
}
Write-Host "OK artifacts"

Write-Host ""
Write-Host "[2/4] docker compose config" -ForegroundColor Cyan
$composeFile = "infra/platform/docker-compose.yml"
docker compose --env-file .env -f $composeFile config --quiet
if ($LASTEXITCODE -ne 0) {
  throw "compose config failed"
}
Write-Host "OK compose config"

Write-Host ""
Write-Host "[3/4] pytest apps/api (incl. failure A-E)" -ForegroundColor Cyan
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
Write-Host "[4/4] fake-cs2 self-test" -ForegroundColor Cyan
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
Write-Host "VERIFY OK — TZ002 primary GATE (Fake)" -ForegroundColor Green
Write-Host "live_smoke=blocked (no VPS / @owner SSH)" -ForegroundColor Yellow
exit 0
