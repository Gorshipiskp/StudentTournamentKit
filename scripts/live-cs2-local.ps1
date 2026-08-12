# STK live-cs2-local (TZ009) - one script for real CS2 DS + Bridge + Platform
# From repo root:
#   .\scripts\live-cs2-local.ps1
#   .\scripts\live-cs2-local.ps1 -MatchId m_live_cs2
#
# Loads root .env, starts API + dashboard + overlay + judge + director-agent,
# creates match, register/assign, start-live (NOT Fake), staff-links,
# writes Bridge config.json on DS, starts dedicated if needed.
# You: connect 127.0.0.1:27015 and play a round (solo + bots OK).
# NOTE: ASCII-only messages so Windows PowerShell parses the file reliably.

[CmdletBinding()]
param(
    [string]$MatchId = "m_live_cs2",
    [string]$ServerId = "srv_local",
    [string]$MapName = "de_dust2",
    [switch]$SkipMigrate,
    [switch]$SkipDashboard,
    [switch]$SkipOverlay,
    [switch]$SkipJudge,
    [switch]$SkipAgent,
    [switch]$SkipDsStart,
    [switch]$AllowLocalDb,
    [switch]$AllowFakeAgent,
    [string]$ObsPassword = ""
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Lib = Join-Path $PSScriptRoot "lib/Import-DotEnv.ps1"
. $Lib

$EnvFile = Join-Path $Root ".env"
if (-not (Test-Path $EnvFile)) {
    throw "Missing root .env - copy .env.example and set MYSQL_* / CS2_*."
}
Import-StkDotEnv -Path $EnvFile

$mysqlHost = $env:MYSQL_HOST
if ([string]::IsNullOrWhiteSpace($mysqlHost)) {
    throw "MYSQL_HOST is empty in .env"
}
if ($mysqlHost -eq "mysql") {
    throw "MYSQL_HOST=mysql is for Docker Compose only. Use remote host or 127.0.0.1 + compose."
}
if (-not $AllowLocalDb -and ($mysqlHost -eq "127.0.0.1" -or $mysqlHost -eq "localhost")) {
    throw "MYSQL_HOST=$mysqlHost looks local. Use remote MySQL or pass -AllowLocalDb."
}

$apiPort = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
$apiBase = "http://127.0.0.1:$apiPort"
$bridgePort = if ($env:STK_BRIDGE_COMMAND_PORT) { $env:STK_BRIDGE_COMMAND_PORT } else { "27099" }
$bridgeUrl = if ($env:CS2_GAME_ENDPOINT_URL) {
    $env:CS2_GAME_ENDPOINT_URL.Trim().TrimEnd('/')
} else {
    "http://127.0.0.1:$bridgePort"
}
if ([string]::IsNullOrWhiteSpace($env:CS2_WEBHOOK_SECRET)) {
    throw "CS2_WEBHOOK_SECRET missing in .env (required for live HMAC)."
}
$webhookSecret = $env:CS2_WEBHOOK_SECRET
if ([string]::IsNullOrWhiteSpace($env:CS2_INSTALL_DIR)) {
    throw "CS2_INSTALL_DIR missing in .env (see LOCAL-CS2-DS.md)."
}
$cs2Root = $env:CS2_INSTALL_DIR.Trim().TrimEnd('/', '\')
if (-not (Test-Path $cs2Root)) {
    throw "CS2_INSTALL_DIR does not exist: $cs2Root"
}
$organizerUser = if ($env:STK_ORGANIZER_USERNAME) { $env:STK_ORGANIZER_USERNAME } else { "organizer" }
if ([string]::IsNullOrWhiteSpace($env:STK_ORGANIZER_PASSWORD)) {
    throw "STK_ORGANIZER_PASSWORD missing in .env"
}
$organizerPass = $env:STK_ORGANIZER_PASSWORD

$apiDir = Join-Path $Root "apps/api"
$dashboardDir = Join-Path $Root "apps/dashboard"
$overlayDir = Join-Path $Root "apps/overlay"
$judgeDir = Join-Path $Root "apps/judge"
$agentDir = Join-Path $Root "apps/director-agent"
$venvPython = Join-Path $apiDir ".venv/Scripts/python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = "python"
}

$runnerDir = Join-Path $env:TEMP "stk-live-cs2-runners"
New-Item -ItemType Directory -Force -Path $runnerDir | Out-Null
$envBlock = Export-StkDotEnvBlock -Path $EnvFile

function New-RunnerScript {
    param([string]$Name, [string]$WorkDir, [string[]]$Commands)
    $path = Join-Path $runnerDir "$Name.ps1"
    $body = @($envBlock, "Set-Location '$WorkDir'") + $Commands
    Set-Content -LiteralPath $path -Encoding utf8 ($body -join "`n")
    return $path
}

function Test-HttpOk([string]$Url, [int]$TimeoutSec = 2) {
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
        return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
    }
    catch {
        return $false
    }
}

function Wait-HttpOk([string]$Url, [string]$Label, [int]$Seconds = 90) {
    Write-Host ("Waiting for {0} ..." -f $Label) -ForegroundColor Cyan
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-HttpOk $Url) {
            Write-Host ("OK {0}" -f $Label) -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "Timeout: $Label ($Url)"
}

function Ensure-NpmDeps {
    param([string]$AppDir, [string]$Label)
    $nm = Join-Path $AppDir "node_modules"
    if (-not (Test-Path $nm)) {
        Write-Host ("npm install in {0} ..." -f $Label) -ForegroundColor Yellow
        Push-Location $AppDir
        try {
            npm install
            if ($LASTEXITCODE -ne 0) { throw "npm install failed in $AppDir" }
        }
        finally { Pop-Location }
    }
}

function Start-ViteDev {
    param([string]$Name, [string]$Dir, [string]$Port, [string]$Label, [string]$Origin)
    if (Test-HttpOk $Origin 1) {
        Write-Host ("{0} already at {1}" -f $Label, $Origin) -ForegroundColor Green
        return
    }
    Ensure-NpmDeps -AppDir $Dir -Label $Label
    $runner = New-RunnerScript -Name $Name -WorkDir $Dir -Commands @(
        "Write-Host '$Label vite :$Port' -ForegroundColor Cyan"
        "npm run dev"
    )
    Start-Process powershell -ArgumentList @("-NoExit", "-File", $runner) | Out-Null
    Write-Host ("Started {0} window" -f $Label) -ForegroundColor Green
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
        throw "stk-director-agent.exe missing and Go not in PATH. Install Go or build in apps/director-agent."
    }
    Write-Host "Building stk-director-agent.exe ..." -ForegroundColor Yellow
    Push-Location $agentDir
    try {
        go build -o stk-director-agent.exe ./cmd/agent
        if ($LASTEXITCODE -ne 0) { throw "go build director-agent failed" }
    }
    finally { Pop-Location }
    return $exe
}

function Invoke-Json {
    param(
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [object]$Body = $null
    )
    $params = @{
        Method          = $Method
        Uri             = $Url
        Headers         = $Headers
        UseBasicParsing = $true
    }
    if ($null -ne $Body) {
        $params.ContentType = "application/json"
        $params.Body = ($Body | ConvertTo-Json -Compress -Depth 6)
    }
    try {
        return Invoke-RestMethod @params
    }
    catch {
        $resp = $_.Exception.Response
        $code = if ($resp) { [int]$resp.StatusCode } else { 0 }
        $detail = $_.ErrorDetails.Message
        return [pscustomobject]@{ __error = $true; status = $code; detail = $detail; exception = $_.Exception.Message }
    }
}

Write-Host ""
Write-Host "== STK live-cs2-local ==" -ForegroundColor Cyan
Write-Host ("MatchId={0} ServerId={1} API={2} Bridge={3}" -f $MatchId, $ServerId, $apiBase, $bridgeUrl)
Write-Host ("MySQL host from .env: {0}" -f $mysqlHost) -ForegroundColor DarkGray

# --- API ---
if (-not (Test-HttpOk "$apiBase/health")) {
    if (-not $SkipMigrate -and (Test-Path (Join-Path $apiDir ".venv/Scripts/python.exe"))) {
        Write-Host "Alembic upgrade ..." -ForegroundColor Cyan
        Push-Location $apiDir
        try {
            & $venvPython -m alembic upgrade head
            if ($LASTEXITCODE -ne 0) { throw "alembic failed" }
        }
        finally { Pop-Location }
    }
    $apiRunner = New-RunnerScript -Name "stk-api" -WorkDir $apiDir -Commands @(
        "Write-Host 'API uvicorn :$apiPort' -ForegroundColor Cyan"
        "& '$venvPython' -m uvicorn app.main:app --host 127.0.0.1 --port $apiPort --reload"
    )
    Start-Process powershell -ArgumentList @("-NoExit", "-File", $apiRunner) | Out-Null
    Write-Host "Started API window" -ForegroundColor Green
}
else {
    Write-Host "API already up (/health)" -ForegroundColor Green
}

Wait-HttpOk "$apiBase/ready" "API /ready (database)" 120

# --- Dashboard / overlay / judge ---
$dashOrigin = if ($env:STK_DASHBOARD_ORIGIN) { $env:STK_DASHBOARD_ORIGIN } else { "http://127.0.0.1:5174" }
$watchOrigin = if ($env:STK_WATCH_ORIGIN) { $env:STK_WATCH_ORIGIN } else { "http://127.0.0.1:5173" }
$judgeOrigin = if ($env:STK_JUDGE_ORIGIN) { $env:STK_JUDGE_ORIGIN } else { "http://127.0.0.1:5175" }

if (-not $SkipDashboard) {
    if (-not (Test-HttpOk $dashOrigin 1)) {
        Ensure-NpmDeps -AppDir $dashboardDir -Label "dashboard"
        $dashRunner = New-RunnerScript -Name "stk-dashboard" -WorkDir $dashboardDir -Commands @(
            "Write-Host 'dashboard vite :5174' -ForegroundColor Cyan"
            "npm run dev"
        )
        Start-Process powershell -ArgumentList @("-NoExit", "-File", $dashRunner) | Out-Null
        Write-Host "Started dashboard window" -ForegroundColor Green
    }
    else {
        Write-Host "Dashboard already at $dashOrigin" -ForegroundColor Green
    }
}

if (-not $SkipOverlay) {
    Start-ViteDev -Name "stk-overlay" -Dir $overlayDir -Port "5173" -Label "overlay/watch" -Origin $watchOrigin
}
if (-not $SkipJudge) {
    Start-ViteDev -Name "stk-judge" -Dir $judgeDir -Port "5175" -Label "judge" -Origin $judgeOrigin
}

# --- Auth ---
$login = Invoke-Json -Method POST -Url "$apiBase/api/v1/auth/login" -Body @{
    username = $organizerUser
    password = $organizerPass
}
if ($login.__error) {
    throw "Organizer login failed. Check STK_ORGANIZER_* in .env. $($login.detail)"
}
$token = $login.access_token
$auth = @{ Authorization = "Bearer $token" }

# --- Match ---
$existing = Invoke-Json -Method GET -Url "$apiBase/api/v1/matches/$MatchId"
if ($existing.__error -and $existing.status -eq 404) {
    Write-Host "Creating match $MatchId ..." -ForegroundColor Cyan
    $created = Invoke-Json -Method POST -Url "$apiBase/api/v1/matches" -Body @{
        match_id          = $MatchId
        map_name          = $MapName
        webhook_secret    = $webhookSecret
        game_endpoint_url = $bridgeUrl
    }
    if ($created.__error) { throw "Create match failed: $($created.detail)" }
}
elseif ($existing.__error) {
    throw "GET match failed: $($existing.detail)"
}
else {
    Write-Host "Match $MatchId already exists" -ForegroundColor Green
}

# --- Game server ---
$servers = Invoke-Json -Method GET -Url "$apiBase/api/v1/game-servers"
$haveServer = $false
if (-not $servers.__error -and $servers.items) {
    $haveServer = @($servers.items | Where-Object { $_.id -eq $ServerId }).Count -gt 0
}
if (-not $haveServer) {
    Write-Host "Registering game-server $ServerId ..." -ForegroundColor Cyan
    $reg = Invoke-Json -Method POST -Url "$apiBase/api/v1/game-servers" -Body @{
        server_id      = $ServerId
        endpoint_url   = $bridgeUrl
        webhook_secret = $webhookSecret
        host           = "127.0.0.1"
        port           = 27015
    }
    if ($reg.__error -and $reg.status -ne 409) {
        throw "Register server failed: $($reg.detail)"
    }
}
else {
    Write-Host "Game-server $ServerId already registered" -ForegroundColor Green
}

# --- Assign + start-live (NOT Fake /start) ---
Write-Host "assign-server -> start-live (real path) ..." -ForegroundColor Cyan
# force=true: steal srv_local from a previous MatchId (common re-run / -MatchId change)
$assign = Invoke-Json -Method POST -Url "$apiBase/api/v1/matches/$MatchId/assign-server" `
    -Headers $auth -Body @{ server_id = $ServerId; force = $true }
if ($assign.__error) { throw "assign-server failed: $($assign.detail)" }

$start = Invoke-Json -Method POST -Url "$apiBase/api/v1/matches/$MatchId/start-live" `
    -Headers $auth -Body @{ server_id = $ServerId }
if ($start.__error) { throw "start-live failed: $($start.detail)" }
$gs = $start.match.game_server_id
if (-not $gs -or $gs -eq "srv_fake" -or ($gs -like "srv_fake*")) {
    throw "Refusing Fake server id ($gs). Use start-live + real Bridge, not Fake start."
}
Write-Host ("Match LIVE (not Fake): status={0} server={1}" -f $start.match.status, $gs) -ForegroundColor Green

# --- Staff links (director / judge / commentator watch) ---
Write-Host "Creating staff-links ..." -ForegroundColor Cyan
$staff = Invoke-Json -Method POST -Url "$apiBase/api/v1/matches/$MatchId/staff-links" -Headers $auth
if ($staff.__error) {
    Write-Host ("WARN: staff-links failed: {0}" -f $staff.detail) -ForegroundColor Yellow
    $staff = $null
}

# --- Director Agent (real OBS scenes; WHIP for commentators — no --live-webrtc) ---
if (-not $SkipAgent) {
    try {
        $agentToken = if ($env:STK_AGENT_TOKEN) { $env:STK_AGENT_TOKEN } else { "dev_agent_token_change_me" }
        # Prefer -ObsPassword flag; else STK_OBS_PASSWORD from root .env (must be uncommented)
        $obsPass = $ObsPassword
        if ([string]::IsNullOrWhiteSpace($obsPass) -and -not [string]::IsNullOrWhiteSpace($env:STK_OBS_PASSWORD)) {
            $obsPass = $env:STK_OBS_PASSWORD.Trim()
        }
        $obsUrl = if (-not [string]::IsNullOrWhiteSpace($env:STK_OBS_URL)) {
            $env:STK_OBS_URL.Trim()
        } else {
            "ws://127.0.0.1:4455"
        }

        $useFake = [bool]$AllowFakeAgent
        if ([string]::IsNullOrWhiteSpace($obsPass)) {
            if (-not $AllowFakeAgent) {
                throw @"
STK_OBS_PASSWORD is empty. Live path needs real OBS (no silent --fake-obs).
1) In root .env uncomment and set:
   STK_OBS_URL=ws://127.0.0.1:4455
   STK_OBS_PASSWORD=your_obs_websocket_password
2) Or pass -ObsPassword '...'
3) Or -AllowFakeAgent for GATE-only fake-obs/fake-webrtc
"@
            }
            $useFake = $true
        }

        $agentExe = Ensure-DirectorAgentExe
        $agentCmd = "& '$agentExe' --platform '$apiBase' --match '$MatchId' --token '$agentToken'"
        if ($useFake) {
            $agentCmd += " --fake-obs --fake-webrtc"
            $agentMode = "ALLOW FAKE: fake-obs + fake-webrtc (use /watch?media=fake)"
        }
        else {
            $escapedObs = $obsPass -replace "'", "''"
            $escapedUrl = $obsUrl -replace "'", "''"
            # Scenes only — live video = OBS WHIP (TZ011); do not start --live-webrtc
            $agentCmd += " --obs-url '$escapedUrl' --obs-password '$escapedObs'"
            $agentMode = "OBS WebSocket scenes only (WHIP for /watch — no live-webrtc)"
        }
        $agentRunner = New-RunnerScript -Name "stk-agent" -WorkDir $agentDir -Commands @(
            "Write-Host 'Director Agent ($agentMode) match=$MatchId' -ForegroundColor Cyan"
            $agentCmd
        )
        Start-Process powershell -ArgumentList @("-NoExit", "-File", $agentRunner) | Out-Null
        Write-Host ("Started director-agent window ({0})" -f $agentMode) -ForegroundColor Green
    }
    catch {
        Write-Host ("WARN: director-agent not started: {0}" -f $_.Exception.Message) -ForegroundColor Yellow
        Write-Host "  Build manually: cd apps/director-agent; go build -o stk-director-agent.exe ./cmd/agent" -ForegroundColor DarkGray
    }
}
# --- Bridge config from .env ---
$cfgObj = [ordered]@{
    PlatformUrl              = $apiBase
    WebhookSecret            = $webhookSecret
    MatchId                  = $MatchId
    ServerId                 = $ServerId
    ProtocolVersion          = "1"
    BridgeVersion            = "0.2.0"
    HeartbeatIntervalSeconds = 15
    CommandListenHost        = "127.0.0.1"
    CommandListenPort        = [int]$bridgePort
    EventsPath               = "/api/v1/internal/cs2/events"
}
$cfgJson = ($cfgObj | ConvertTo-Json -Depth 4)

$repoCfg = Join-Path $Root "infra/game-server/plugins/STK.Bridge/config.json"
Set-Content -LiteralPath $repoCfg -Value $cfgJson -Encoding utf8
Write-Host "Updated repo Bridge config.json" -ForegroundColor Green

$dsPlugin = Join-Path $cs2Root "game\csgo\addons\counterstrikesharp\plugins\STK.Bridge"
if (Test-Path (Split-Path $dsPlugin -Parent)) {
    New-Item -ItemType Directory -Force -Path $dsPlugin | Out-Null
    $dsCfg = Join-Path $dsPlugin "config.json"
    Set-Content -LiteralPath $dsCfg -Value $cfgJson -Encoding utf8
    Write-Host "Updated DS Bridge config: $dsCfg" -ForegroundColor Green
}
else {
    Write-Host "WARN: DS plugin path not found ($dsPlugin). Check CS2_INSTALL_DIR." -ForegroundColor Yellow
}

# --- Dedicated ---
$bridgeUp = Test-HttpOk "$bridgeUrl/health"
if (-not $bridgeUp -and -not $SkipDsStart) {
    $batCasual = Join-Path $cs2Root "start-dedicated.bat"
    $batComp = Join-Path $cs2Root "start-dedicated-competitive.bat"
    # Casual + bots is best for solo smoke
    $bat = if (Test-Path $batCasual) { $batCasual } elseif (Test-Path $batComp) { $batComp } else { $null }
    if ($bat) {
        Write-Host "Bridge down - starting dedicated: $bat" -ForegroundColor Cyan
        Start-Process -FilePath $bat -WorkingDirectory $cs2Root
        Write-Host "Waiting for Bridge :$bridgePort (up to 90s). Restart DS manually if config just changed." -ForegroundColor Yellow
        try {
            Wait-HttpOk "$bridgeUrl/health" "Bridge /health" 90
            $bridgeUp = $true
        }
        catch {
            Write-Host "Bridge still down. Start/restart dedicated yourself, then connect." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "No start-dedicated.bat in $cs2Root - start DS yourself." -ForegroundColor Yellow
    }
}
elseif ($bridgeUp) {
    Write-Host "Bridge already up. If MatchId just changed - RESTART dedicated to reload config." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Ready (real Bridge, not Fake) ===" -ForegroundColor Green
Write-Host "1. If Bridge still has old MatchId - restart the dedicated window."
Write-Host "2. In CS2:  connect 127.0.0.1:27015"
Write-Host "3. Play a round (bots OK)."
Write-Host "4. Score:   $apiBase/api/v1/matches/$MatchId"
Write-Host "5. Admin:   $dashOrigin/admin  (user: $organizerUser)"
Write-Host ("6. Overlay: {0}/overlay/{1}" -f $watchOrigin, $MatchId)
Write-Host ("7. Director panel: {0}/director/{1}" -f $dashOrigin, $MatchId)
Write-Host ""
Write-Host "Commentator video (TZ011 WHIP canon):" -ForegroundColor Cyan
Write-Host "  MediaMTX:  docker compose --env-file .env -f infra/platform/docker-compose.yml --profile whip up -d mediamtx"
Write-Host "  WHIP URL:  POST $apiBase/api/v1/matches/$MatchId/whip-publish  (Bearer organizer)"
Write-Host "  Then OBS → Stream → Service WHIP → paste whip_url + bearer → Start Streaming"
Write-Host ("  Watch:     {0}/watch?token=<from staff commentator link>" -f $watchOrigin)
Write-Host "  Fake path: /watch?media=fake  (only with --fake-webrtc agent)"
if ($staff -and -not $staff.__error) {
    Write-Host ""
    Write-Host "Staff links (open these):" -ForegroundColor Cyan
    Write-Host ("  director     {0}" -f $staff.director_url)
    Write-Host ("  judge        {0}" -f $staff.judge.url)
    Write-Host ("  commentator  {0}" -f $staff.commentator.url)
}
else {
    Write-Host "Staff links: admin -> match -> staff links (or POST .../staff-links)" -ForegroundColor DarkGray
}
if ($SkipAgent) {
    $agentToken = if ($env:STK_AGENT_TOKEN) { $env:STK_AGENT_TOKEN } else { "dev_agent_token_change_me" }
    Write-Host ""
    Write-Host "Agent (manual):" -ForegroundColor DarkGray
    Write-Host "  cd apps/director-agent" -ForegroundColor DarkGray
    Write-Host ("  .\stk-director-agent.exe --platform {0} --match {1} --token {2} --fake-obs --fake-webrtc" -f $apiBase, $MatchId, $agentToken) -ForegroundColor DarkGray
}
Write-Host ""
Write-Host "Secrets/paths from root .env (CS2_WEBHOOK_SECRET, CS2_INSTALL_DIR, MYSQL_*)." -ForegroundColor DarkGray
Write-Host "Keep API/dashboard/overlay/judge/agent windows open. Stop with Ctrl+C in each." -ForegroundColor DarkGray
Write-Host "Flags: -SkipOverlay -SkipJudge -SkipAgent -SkipDashboard -SkipDsStart -AllowFakeAgent -ObsPassword (or uncomment STK_OBS_PASSWORD in .env)" -ForegroundColor DarkGray
if ($bridgeUp) {
    try {
        $h = Invoke-RestMethod "$bridgeUrl/health"
        Write-Host ("Bridge health: role={0} match_id={1} server_id={2} seq={3}" -f $h.role, $h.match_id, $h.server_id, $h.last_sequence) -ForegroundColor Cyan
        if ($h.role -ne "stk-bridge") {
            Write-Host "ERROR: expected role=stk-bridge (got $($h.role)) - Fake must not be on :$bridgePort" -ForegroundColor Red
        }
        if ($h.match_id -ne $MatchId -or $h.server_id -ne $ServerId) {
            Write-Host "WARN: Bridge still has old ids - RESTART dedicated after config write." -ForegroundColor Red
        }
    }
    catch { }
}
