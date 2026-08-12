# STK dev stack - remote MySQL + API on host + Vite (overlay/dashboard)
# Usage (from repo root or scripts/):
#   .\scripts\dev-remote.ps1
#   .\scripts\dev-remote.ps1 -MatchId m_live
#   .\scripts\dev-remote.ps1 -ApiOnly
#
# Requires root .env with remote MYSQL_* (not MYSQL_HOST=mysql). MYSQL_SSL=1 for Timeweb.

[CmdletBinding()]
param(
    [string]$MatchId = "m_dev",
    [switch]$ApiOnly,
    [switch]$SkipMigrate,
    [switch]$AllowLocalDb
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Lib = Join-Path $PSScriptRoot "lib/Import-DotEnv.ps1"
if (-not (Test-Path $Lib)) {
    throw "missing $Lib"
}
. $Lib

$EnvFile = Join-Path $Root ".env"
$EnvExample = Join-Path $Root ".env.example"
if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Write-Host "No .env - copying .env.example" -ForegroundColor Yellow
        Copy-Item $EnvExample $EnvFile
    }
    else {
        throw ".env and .env.example missing"
    }
}

Import-StkDotEnv -Path $EnvFile

$mysqlHost = $env:MYSQL_HOST
if ([string]::IsNullOrWhiteSpace($mysqlHost)) {
    throw "MYSQL_HOST is empty in .env"
}
if ($mysqlHost -eq "mysql") {
    throw "MYSQL_HOST=mysql is for Docker Compose only. Set remote host in .env (e.g. xxxx.twc1.net) and MYSQL_SSL=1. Local MySQL: docker compose + verify.ps1, not dev-remote.ps1."
}
if (-not $AllowLocalDb -and ($mysqlHost -eq "127.0.0.1" -or $mysqlHost -eq "localhost")) {
    throw "MYSQL_HOST=$mysqlHost looks like local DB. dev-remote.ps1 is for remote MySQL. Fix .env or pass -AllowLocalDb."
}

$sslFlag = if ($env:MYSQL_SSL) { $env:MYSQL_SSL.Trim().ToLower() } else { "" }
$sslOn = @("1", "true", "yes", "required") -contains $sslFlag
if ($sslOn) {
    $ca = if ($env:MYSQL_SSL_CA) { $env:MYSQL_SSL_CA.Trim() } else { "" }
    if ($ca -and -not (Test-Path $ca)) {
        Write-Host "WARN: MYSQL_SSL_CA not found: $ca" -ForegroundColor Yellow
    }
}
elseif ($mysqlHost -notmatch "^(127\.0\.0\.1|localhost)$") {
    Write-Host "WARN: remote MYSQL_HOST but MYSQL_SSL is off - Timeweb may require MYSQL_SSL=1" -ForegroundColor Yellow
}

$apiPort = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
$apiDir = Join-Path $Root "apps/api"
$overlayDir = Join-Path $Root "apps/overlay"
$dashboardDir = Join-Path $Root "apps/dashboard"
$venvPython = Join-Path $apiDir ".venv/Scripts/python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating apps/api/.venv ..." -ForegroundColor Yellow
    Push-Location $apiDir
    try {
        python -m venv .venv
        & .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
        if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
    }
    finally {
        Pop-Location
    }
}

if (-not $SkipMigrate) {
    Write-Host "Alembic upgrade (remote DB) ..." -ForegroundColor Cyan
    Push-Location $apiDir
    try {
        & $venvPython -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw "alembic upgrade failed" }
    }
    finally {
        Pop-Location
    }
    Write-Host "OK migrations" -ForegroundColor Green
}

$runnerDir = Join-Path $env:TEMP "stk-dev-runners"
New-Item -ItemType Directory -Force -Path $runnerDir | Out-Null
$envBlock = Export-StkDotEnvBlock -Path $EnvFile

function New-RunnerScript {
    param(
        [string]$Name,
        [string]$WorkDir,
        [string[]]$Commands
    )
    $path = Join-Path $runnerDir "$Name.ps1"
    $body = @(
        $envBlock
        "Set-Location '$WorkDir'"
    ) + $Commands
    Set-Content -LiteralPath $path -Encoding UTF8 ($body -join "`n")
    return $path
}

Write-Host ""
Write-Host "== STK dev-remote ==" -ForegroundColor Cyan
$mysqlPort = if ($env:MYSQL_PORT) { $env:MYSQL_PORT } else { "3306" }
$mysqlDb = if ($env:MYSQL_DATABASE) { $env:MYSQL_DATABASE } else { "stk" }
Write-Host ("MySQL: {0}:{1}/{2}" -f $mysqlHost, $mysqlPort, $mysqlDb)

$apiRunner = New-RunnerScript -Name "stk-api" -WorkDir $apiDir -Commands @(
    "Write-Host 'API uvicorn :$apiPort (reload)' -ForegroundColor Cyan"
    "& '$venvPython' -m uvicorn app.main:app --host 127.0.0.1 --port $apiPort --reload"
)
Start-Process powershell -ArgumentList @("-NoExit", "-File", $apiRunner) | Out-Null
Write-Host "Started API window" -ForegroundColor Green

if (-not $ApiOnly) {
    foreach ($pair in @(
            @{ Name = "stk-overlay"; Dir = $overlayDir; Port = "5173"; Label = "overlay" },
            @{ Name = "stk-dashboard"; Dir = $dashboardDir; Port = "5174"; Label = "dashboard" }
        )) {
        $nm = Join-Path $pair.Dir "node_modules"
        if (-not (Test-Path $nm)) {
            Write-Host ("npm install in {0} ..." -f $pair.Label) -ForegroundColor Yellow
            Push-Location $pair.Dir
            try {
                npm install
                if ($LASTEXITCODE -ne 0) { throw "npm install failed in $($pair.Dir)" }
            }
            finally {
                Pop-Location
            }
        }
        $runner = New-RunnerScript -Name $pair.Name -WorkDir $pair.Dir -Commands @(
            "Write-Host '$($pair.Label) vite :$($pair.Port)' -ForegroundColor Cyan"
            "npm run dev"
        )
        Start-Process powershell -ArgumentList @("-NoExit", "-File", $runner) | Out-Null
        Write-Host ("Started {0} window" -f $pair.Label) -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host ("  health   http://127.0.0.1:{0}/health" -f $apiPort)
Write-Host ("  ready    http://127.0.0.1:{0}/ready" -f $apiPort)
if (-not $ApiOnly) {
    Write-Host ("  overlay  http://127.0.0.1:5173/overlay/{0}" -f $MatchId)
    Write-Host ("  director http://127.0.0.1:5174/director/{0}" -f $MatchId)
}
Write-Host ""
Write-Host "Create match: POST http://127.0.0.1:$apiPort/api/v1/matches (see scripts/README.md)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Agent (separate terminal, after OBS scenes):" -ForegroundColor DarkGray
$agentToken = if ($env:STK_AGENT_TOKEN) { $env:STK_AGENT_TOKEN } else { "dev_agent_token_change_me" }
Write-Host "  cd apps/director-agent" -ForegroundColor DarkGray
Write-Host "  .\stk-director-agent.exe --platform http://127.0.0.1:$apiPort --match $MatchId --token $agentToken --obs-url ws://127.0.0.1:4455 --obs-password YOUR_OBS_PASSWORD" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Stop: close the opened PowerShell windows (Ctrl+C in each)." -ForegroundColor Yellow
