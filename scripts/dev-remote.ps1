# STK dev stack - remote MySQL + API + Vite apps + optional Director Agent + MediaMTX
# Usage (from repo root or scripts/):
#   .\scripts\dev-remote.ps1
#   .\scripts\dev-remote.ps1 -MatchId m_live
#   .\scripts\dev-remote.ps1 -ApiOnly
#   .\scripts\dev-remote.ps1 -ObsPassword "your_obs_ws_password"   # real OBS instead of --fake-obs
#   .\scripts\dev-remote.ps1 -SkipAgent                              # no agent window
#   .\scripts\dev-remote.ps1 -SkipMediamtx                           # no WHIP/WHEP (Docker MediaMTX)
#
# Requires root .env with remote MYSQL_* (not MYSQL_HOST=mysql). MYSQL_SSL=1 for Timeweb.

[CmdletBinding()]
param(
    [string]$MatchId = "m_dev",
    [switch]$ApiOnly,
    [switch]$SkipMigrate,
    [switch]$AllowLocalDb,
    [switch]$SkipAgent,
    [switch]$SkipMediamtx,
    [string]$ObsPassword = ""
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
$judgeDir = Join-Path $Root "apps/judge"
$agentDir = Join-Path $Root "apps/director-agent"
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

function Ensure-NpmDeps {
    param(
        [string]$AppDir,
        [string]$Label
    )
    $nm = Join-Path $AppDir "node_modules"
    if (-not (Test-Path $nm)) {
        Write-Host ("npm install in {0} ..." -f $Label) -ForegroundColor Yellow
        Push-Location $AppDir
        try {
            npm install
            if ($LASTEXITCODE -ne 0) { throw "npm install failed in $AppDir" }
        }
        finally {
            Pop-Location
        }
    }
}

function Ensure-DirectorAgentExe {
    $exe = Join-Path $agentDir "stk-director-agent.exe"
    if (Test-Path $exe) {
        return $exe
    }
    $goCmd = Get-Command go -ErrorAction SilentlyContinue
    if (-not $goCmd) {
        $goExe = "C:\Program Files\Go\bin\go.exe"
        if (Test-Path $goExe) {
            $env:Path = "C:\Program Files\Go\bin;" + $env:Path
            $goCmd = Get-Command go -ErrorAction SilentlyContinue
        }
    }
    if (-not $goCmd) {
        throw "stk-director-agent.exe missing and Go not in PATH. Install Go 1.22+ or build manually in apps/director-agent."
    }
    Write-Host "Building stk-director-agent.exe ..." -ForegroundColor Yellow
    Push-Location $agentDir
    try {
        go build -o stk-director-agent.exe ./cmd/agent
        if ($LASTEXITCODE -ne 0) { throw "go build director-agent failed" }
    }
    finally {
        Pop-Location
    }
    return $exe
}

function Start-ViteDev {
    param(
        [string]$Name,
        [string]$Dir,
        [string]$Port,
        [string]$Label
    )
    Ensure-NpmDeps -AppDir $Dir -Label $Label
    $runner = New-RunnerScript -Name $Name -WorkDir $Dir -Commands @(
        "Write-Host '$Label vite :$Port' -ForegroundColor Cyan"
        "npm run dev"
    )
    Start-Process powershell -ArgumentList @("-NoExit", "-File", $runner) | Out-Null
    Write-Host ("Started {0} window" -f $Label) -ForegroundColor Green
}

function Start-Mediamtx {
    $composeFile = Join-Path $Root "infra/platform/docker-compose.yml"
    $webrtcPort = if ($env:MEDIAMTX_WEBRTC_PORT) { $env:MEDIAMTX_WEBRTC_PORT.Trim() } else { "8889" }
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerCmd) {
        Write-Host "WARN: Docker not in PATH — MediaMTX skipped (WHEP on :$webrtcPort will refuse)." -ForegroundColor Yellow
        Write-Host "  Install Docker Desktop, then re-run or:" -ForegroundColor DarkGray
        Write-Host "  docker compose --env-file .env -f infra/platform/docker-compose.yml --profile whip up -d mediamtx" -ForegroundColor DarkGray
        return $false
    }
    Write-Host "MediaMTX (WHIP/WHEP :$webrtcPort) ..." -ForegroundColor Cyan
    Push-Location $Root
    try {
        docker compose --env-file $EnvFile -f $composeFile --profile whip up -d mediamtx
        if ($LASTEXITCODE -ne 0) {
            Write-Host "WARN: MediaMTX compose failed (exit $LASTEXITCODE). /watch WHEP needs :$webrtcPort." -ForegroundColor Yellow
            return $false
        }
    }
    finally {
        Pop-Location
    }
    Write-Host ("OK MediaMTX  http://127.0.0.1:{0}/stk/<matchId>/whep" -f $webrtcPort) -ForegroundColor Green
    return $true
}

Write-Host ""
Write-Host "== STK dev-remote ==" -ForegroundColor Cyan
$mysqlPort = if ($env:MYSQL_PORT) { $env:MYSQL_PORT } else { "3306" }
$mysqlDb = if ($env:MYSQL_DATABASE) { $env:MYSQL_DATABASE } else { "stk" }
Write-Host ("MySQL: {0}:{1}/{2}" -f $mysqlHost, $mysqlPort, $mysqlDb)

$mediamtxUp = $false
if (-not $SkipMediamtx) {
    $mediamtxUp = Start-Mediamtx
}
else {
    Write-Host "MediaMTX skipped (-SkipMediamtx)" -ForegroundColor DarkGray
}

$apiRunner = New-RunnerScript -Name "stk-api" -WorkDir $apiDir -Commands @(
    "Write-Host 'API uvicorn :$apiPort (reload)' -ForegroundColor Cyan"
    "& '$venvPython' -m uvicorn app.main:app --host 127.0.0.1 --port $apiPort --reload"
)
Start-Process powershell -ArgumentList @("-NoExit", "-File", $apiRunner) | Out-Null
Write-Host "Started API window" -ForegroundColor Green

if (-not $ApiOnly) {
    Start-ViteDev -Name "stk-overlay" -Dir $overlayDir -Port "5173" -Label "overlay"
    Start-ViteDev -Name "stk-dashboard" -Dir $dashboardDir -Port "5174" -Label "dashboard"
    Start-ViteDev -Name "stk-judge" -Dir $judgeDir -Port "5175" -Label "judge"

    if (-not $SkipAgent) {
        $agentToken = if ($env:STK_AGENT_TOKEN) { $env:STK_AGENT_TOKEN } else { "dev_agent_token_change_me" }
        $agentExe = Ensure-DirectorAgentExe
        $platformUrl = "http://127.0.0.1:$apiPort"
        $obsPass = $ObsPassword
        if ([string]::IsNullOrWhiteSpace($obsPass) -and -not [string]::IsNullOrWhiteSpace($env:STK_OBS_PASSWORD)) {
            $obsPass = $env:STK_OBS_PASSWORD
        }
        $obsUrl = if (-not [string]::IsNullOrWhiteSpace($env:STK_OBS_URL)) {
            $env:STK_OBS_URL.Trim()
        } else {
            "ws://127.0.0.1:4455"
        }
        $agentCmd = "& '$agentExe' --platform '$platformUrl' --match '$MatchId' --token '$agentToken'"
        if (-not [string]::IsNullOrWhiteSpace($obsPass)) {
            $escapedObs = $obsPass -replace "'", "''"
            $escapedUrl = $obsUrl -replace "'", "''"
            # Real OBS: scenes only. Live /watch = WHIP (not --live-webrtc / not silent fake-webrtc).
            $agentCmd += " --obs-url '$escapedUrl' --obs-password '$escapedObs'"
            $agentMode = "OBS WebSocket scenes only (WHIP for /watch)"
        }
        else {
            $agentCmd += " --fake-obs --fake-webrtc"
            $agentMode = "fake-obs + fake-webrtc (set STK_OBS_PASSWORD for real OBS; /watch?media=fake)"
        }
        $agentRunner = New-RunnerScript -Name "stk-agent" -WorkDir $agentDir -Commands @(
            "Write-Host 'Director Agent ($agentMode) match=$MatchId' -ForegroundColor Cyan"
            $agentCmd
        )
        Start-Process powershell -ArgumentList @("-NoExit", "-File", $agentRunner) | Out-Null
        Write-Host "Started director-agent window ($agentMode)" -ForegroundColor Green
    }
}

$dashboardOrigin = if ($env:STK_DASHBOARD_ORIGIN) { $env:STK_DASHBOARD_ORIGIN } else { "http://127.0.0.1:5174" }
$watchOrigin = if ($env:STK_WATCH_ORIGIN) { $env:STK_WATCH_ORIGIN } else { "http://127.0.0.1:5173" }
$judgeOrigin = if ($env:STK_JUDGE_ORIGIN) { $env:STK_JUDGE_ORIGIN } else { "http://127.0.0.1:5175" }
$organizerUser = if ($env:STK_ORGANIZER_USERNAME) { $env:STK_ORGANIZER_USERNAME } else { "organizer" }

Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host ("  health   http://127.0.0.1:{0}/health" -f $apiPort)
Write-Host ("  ready    http://127.0.0.1:{0}/ready" -f $apiPort)
if (-not $ApiOnly) {
    Write-Host ("  admin    {0}/admin  (login: {1})" -f $dashboardOrigin, $organizerUser)
    Write-Host ("  overlay  {0}/overlay/{1}" -f $watchOrigin, $MatchId)
    Write-Host ("  director {0}/director/{1}" -f $dashboardOrigin, $MatchId)
    Write-Host ("  watch    {0}/watch?token=<commentator_invite>  (default WHEP; Fake: &media=fake)" -f $watchOrigin)
    Write-Host ("  judge    {0}/?token=<judge_invite>" -f $judgeOrigin)
}
Write-Host ""
Write-Host "WHIP (live commentators, TZ011):" -ForegroundColor Cyan
$webrtcPort = if ($env:MEDIAMTX_WEBRTC_PORT) { $env:MEDIAMTX_WEBRTC_PORT.Trim() } else { "8889" }
if ($mediamtxUp) {
    Write-Host ("  MediaMTX up  http://127.0.0.1:{0}/stk/<matchId>/whep" -f $webrtcPort)
}
else {
    Write-Host "  docker compose --env-file .env -f infra/platform/docker-compose.yml --profile whip up -d mediamtx"
    if ($SkipMediamtx) {
        Write-Host "  (skipped via -SkipMediamtx)"
    }
}
Write-Host ("  POST http://127.0.0.1:{0}/api/v1/matches/{1}/whip-publish  (organizer Bearer) → OBS WHIP" -f $apiPort, $MatchId)
Write-Host ""
Write-Host "Create match (if needed):" -ForegroundColor DarkGray
Write-Host ("  POST http://127.0.0.1:{0}/api/v1/matches" -f $apiPort) -ForegroundColor DarkGray
Write-Host "  or: admin -> tournament -> bracket -> staff links" -ForegroundColor DarkGray
Write-Host ""
if ($ApiOnly -or $SkipAgent) {
    Write-Host "Agent (manual):" -ForegroundColor DarkGray
    $agentToken = if ($env:STK_AGENT_TOKEN) { $env:STK_AGENT_TOKEN } else { "dev_agent_token_change_me" }
    Write-Host "  cd apps/director-agent" -ForegroundColor DarkGray
    Write-Host "  .\stk-director-agent.exe --platform http://127.0.0.1:$apiPort --match $MatchId --token $agentToken --fake-obs --fake-webrtc" -ForegroundColor DarkGray
    Write-Host "  # real OBS: drop --fake-obs, add --obs-password ..." -ForegroundColor DarkGray
}
Write-Host ""
Write-Host "Flags: -ApiOnly -SkipMigrate -SkipAgent -SkipMediamtx -ObsPassword ... -AllowLocalDb" -ForegroundColor DarkGray
Write-Host "Stop: close the opened PowerShell windows (Ctrl+C in each). MediaMTX: docker compose ... --profile whip stop mediamtx" -ForegroundColor Yellow
