# STK Tournament Alpha — Fake E2E dry-run orchestration (TZ007)
# Composes verify.ps1 + preconditions + human checklist. Does not automate UI or live CS2/Twitch.
param(
    # Optional: alembic upgrade head (needs MySQL reachable from apps/api env)
    [switch]$Migrate,
    # Skip GATE verify (only when iterating human steps; not for acceptance)
    [switch]$SkipVerify,
    [string]$MatchId = "m_alpha"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function Fail([string]$Message, [int]$Code = 1) {
    Write-Host $Message -ForegroundColor Red
    exit $Code
}

Write-Host "== STK alpha-dry-run (TZ007 Tournament Alpha, Fake) ==" -ForegroundColor Cyan
Write-Host ("root: {0}" -f $Root)
Write-Host ("match hint: {0}" -f $MatchId)

# --- Preconditions: .env ---
$EnvFile = Join-Path $Root ".env"
$EnvExample = Join-Path $Root ".env.example"
if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Write-Host "No .env — copying .env.example (dev placeholders)" -ForegroundColor Yellow
        Copy-Item $EnvExample $EnvFile
    }
    else {
        Fail ".env and .env.example missing"
    }
}
Write-Host "OK .env present"

# --- Alpha artifacts (critical) ---
Write-Host ""
Write-Host "[pre] Alpha artifacts" -ForegroundColor Cyan
$alphaRequired = @(
    "docs/ALPHA-RUNBOOK.md",
    "docs/ALPHA-LIVE-TRACKS.md",
    "docs/alpha/organizer.md",
    "docs/alpha/director.md",
    "docs/alpha/judge.md",
    "docs/alpha/POST-MORTEM-TEMPLATE.md",
    "scripts/alpha-dry-run.ps1",
    "workers/developer/notes/TZ007-OWNER-SMOKE.md",
    "workers/developer/notes/TZ007-PROMPT-RUNBOOK.md",
    "tasks/007_TOURNAMENT-ALPHA.md"
)
foreach ($rel in $alphaRequired) {
    $p = Join-Path $Root $rel
    if (-not (Test-Path $p)) {
        Fail "missing required artifact: $rel"
    }
}
Write-Host "OK Alpha artifacts"

# --- Optional migrate ---
if ($Migrate) {
    Write-Host ""
    Write-Host "[migrate] alembic upgrade head" -ForegroundColor Cyan
    $lib = Join-Path $PSScriptRoot "lib/Import-DotEnv.ps1"
    if (Test-Path $lib) {
        . $lib
        Import-StkDotEnv -Path $EnvFile
    }
    $apiDir = Join-Path $Root "apps/api"
    $venvPy = Join-Path $apiDir ".venv/Scripts/python.exe"
    if (-not (Test-Path $venvPy)) {
        Fail "apps/api/.venv missing — run .\scripts\verify.ps1 once or create venv, then retry -Migrate"
    }
    Push-Location $apiDir
    try {
        & $venvPy -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) {
            Fail "alembic upgrade head failed (exit $LASTEXITCODE)" $LASTEXITCODE
        }
    }
    finally {
        Pop-Location
    }
    Write-Host "OK migrate"
}
else {
    Write-Host ""
    Write-Host "[migrate] skipped (pass -Migrate to run alembic upgrade head)" -ForegroundColor DarkGray
}

# --- verify.ps1 (subprocess so its exit does not kill this script early) ---
if (-not $SkipVerify) {
    Write-Host ""
    Write-Host "[verify] calling scripts/verify.ps1" -ForegroundColor Cyan
    $verifyPath = Join-Path $PSScriptRoot "verify.ps1"
    $shell = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }
    $proc = Start-Process -FilePath $shell `
        -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $verifyPath) `
        -Wait -PassThru -NoNewWindow
    if ($null -eq $proc.ExitCode -or $proc.ExitCode -ne 0) {
        $code = if ($null -eq $proc.ExitCode) { 1 } else { $proc.ExitCode }
        Fail "verify.ps1 failed (exit $code) — fix GATE before Alpha dry-run" $code
    }
    Write-Host "OK verify"
}
else {
    Write-Host ""
    Write-Host "[verify] SKIPPED (-SkipVerify) — not valid for owner acceptance" -ForegroundColor Yellow
}

# --- Soft probe: API health (warn only) ---
Write-Host ""
Write-Host "[probe] API http://127.0.0.1:8000/health" -ForegroundColor Cyan
$apiUp = $false
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 3
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) {
        $apiUp = $true
        Write-Host "OK API responds" -ForegroundColor Green
    }
}
catch {
    Write-Host "API not up yet — start stack before human steps (see below)" -ForegroundColor Yellow
}

# --- Human steps (owner / operator) ---
Write-Host ""
Write-Host "== Human Fake E2E (owner) ==" -ForegroundColor Cyan
Write-Host @"

Automated part done (preconditions + verify). Live CS2 / Twitch / real OBS are NOT required.

1) Raise stack (local Fake)
   - MySQL:  docker compose --env-file .env -f infra/platform/docker-compose.yml up -d mysql
   - API:    cd apps/api -> uvicorn (or .\scripts\dev-remote.ps1 -AllowLocalDb -MatchId $MatchId)
   - UI:     dashboard :5174 / overlay :5173 / judge :5175
   - Optional migrate:  .\scripts\alpha-dry-run.ps1 -Migrate

2) Organizer (admin)
   - Open http://127.0.0.1:5174/admin -> login (organizer / from .env)
   - Tournament -> publish -> 4 teams -> bracket -> Start (Fake)
   - Copy staff links (director / judge / watch)
   - Guide: docs/alpha/organizer.md (smoke: TZ005-OWNER-SMOKE.md)

3) Fake CS2 (optional for score/pause; Fake start alone is enough for Alpha primary)
   - tools/fake-cs2 -- see TZ002-OWNER-SMOKE.md

4) Director + Fake OBS
   - Open http://127.0.0.1:5174/director/<matchId>
   - Agent: cd apps/director-agent -> go run ./cmd/agent --fake-obs
     (or stk-director-agent.exe --fake-obs --fake-webrtc)
   - Check health panel + delay checklist + scene changes
   - Guide: docs/alpha/director.md (smoke: TZ006-OWNER-SMOKE.md)

5) Judge
   - Open invite on phone / narrow window -> review -> continue or forfeit
   - Guide: docs/alpha/judge.md (smoke: TZ004-OWNER-SMOKE.md)

6) Overlay / health / audit
   - Overlay: http://127.0.0.1:5173/overlay/<matchId>
   - Watch:   http://127.0.0.1:5173/watch?token=<invite>
   - Judge:   http://127.0.0.1:5175/?token=<invite>
   - GET /api/v1/matches/<id>/health and /audit
   - Acceptance: docs/ALPHA-RUNBOOK.md checklist

URLs (replace <matchId> / tokens):
  http://127.0.0.1:8000/health
  http://127.0.0.1:5174/admin
  http://127.0.0.1:5174/director/$MatchId
  http://127.0.0.1:5173/overlay/$MatchId
  http://127.0.0.1:5173/watch?token=<invite>
  http://127.0.0.1:5175/?token=<invite>

"@

if (-not $apiUp) {
    Write-Host "Hint: API was down during probe - start it before steps 2-6." -ForegroundColor Yellow
}

Write-Host "ALPHA DRY-RUN OK - automated checks passed; finish human checklist for owner sign-off" -ForegroundColor Green
Write-Host "live_cs2 / live_webrtc / live_twitch = blocked (optional tracks)" -ForegroundColor Yellow
Write-Host "Runbook: docs/ALPHA-RUNBOOK.md" -ForegroundColor Yellow
exit 0
