# install-local-cs2-plugins.ps1 — Metamod + CSS + MatchZy + STK.Bridge on @owner Windows CS2 DS
# Usage:
#   .\scripts\install-local-cs2-plugins.ps1
#   .\scripts\install-local-cs2-plugins.ps1 -Cs2Root "Z:\cs2_dedicated_server\steamapps\common\Counter-Strike Global Offensive"

param(
  [string]$Cs2Root = $env:CS2_INSTALL_DIR
)

$ErrorActionPreference = "Stop"

if (-not $Cs2Root) {
  $Cs2Root = "Z:\cs2_dedicated_server\steamapps\common\Counter-Strike Global Offensive"
}

$CsgoDir = Join-Path $Cs2Root "game\csgo"
$GameInfo = Join-Path $CsgoDir "gameinfo.gi"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BridgeProject = Join-Path $RepoRoot "infra\game-server\plugins\STK.Bridge"
$BridgeOut = Join-Path $BridgeProject "bin\Release\net8.0"
$BridgePlugins = Join-Path $CsgoDir "addons\counterstrikesharp\plugins\STK.Bridge"
$TempDir = Join-Path $env:TEMP "stk-cs2-plugins-install"

$MetamodUrl = "https://mms.alliedmods.net/mmsdrop/2.0/mmsource-2.0.0-git1410-windows.zip"
$CssUrl = "https://github.com/roflmuffin/CounterStrikeSharp/releases/download/v1.0.371/counterstrikesharp-with-runtime-windows-1.0.371.zip"
$MatchZyUrl = "https://github.com/shobhit-pathak/MatchZy/releases/download/0.8.15/MatchZy-0.8.15.zip"

function Write-Step($msg) { Write-Host "`n== $msg ==" -ForegroundColor Cyan }
function Ensure-Dir($path) { if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path -Force | Out-Null } }

function Download-File($url, $dest) {
  if ((Test-Path $dest) -and ((Get-Item $dest).Length -gt 0)) {
    Write-Host "  cached: $(Split-Path $dest -Leaf)"
    return
  }
  Write-Host "  download: $url"
  Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
}

function Expand-ZipToCsgo($zipPath) {
  $stage = Join-Path $TempDir ("extract_" + [Guid]::NewGuid().ToString("n"))
  Ensure-Dir $stage
  Expand-Archive -Path $zipPath -DestinationPath $stage -Force
  $addons = Get-ChildItem -Path $stage -Recurse -Directory -Filter "addons" | Select-Object -First 1
  if (-not $addons) {
    throw "No addons/ folder in archive: $zipPath"
  }
  Copy-Item -Path (Join-Path $addons.FullName "*") -Destination (Join-Path $CsgoDir "addons") -Recurse -Force
  Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
}

function Patch-GameInfo {
  if (-not (Test-Path $GameInfo)) { throw "Missing gameinfo.gi: $GameInfo" }
  $content = Get-Content $GameInfo -Raw
  if ($content -match 'Game\s+csgo/addons/metamod') {
    Write-Host "  gameinfo.gi already has metamod path"
    return
  }
  $backup = "$GameInfo.bak-stk-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
  Copy-Item $GameInfo $backup -Force
  Write-Host "  backup: $backup"
  $patched = [regex]::Replace(
    $content,
    '(Game_LowViolence\s+csgo_lv[^\r\n]*)(\r?\n)',
    ('$1$2' + [Environment]::NewLine + "`t`t`tGame`tcsgo/addons/metamod" + [Environment]::NewLine),
    1
  )
  if ($patched -eq $content) {
    throw "gameinfo.gi patch failed — add manually: Game csgo/addons/metamod after Game_LowViolence"
  }
  try {
    Set-Content -Path $GameInfo -Value $patched -NoNewline -Encoding utf8
  }
  catch {
    $pending = "$GameInfo.stk-pending"
    Set-Content -Path $pending -Value $patched -NoNewline -Encoding utf8
    Write-Host "  LOCKED: close CS2 server, then run patch-gameinfo-metamod.bat in CS2 install root" -ForegroundColor Yellow
    Write-Host "  pending patch saved: $pending"
    return
  }
  Write-Host "  patched gameinfo.gi (Metamod search path)"
}

function Build-Bridge {
  $dotnet = "$env:ProgramFiles\dotnet\dotnet.exe"
  if (-not (Test-Path $dotnet)) { throw ".NET SDK not found at $dotnet" }
  Write-Host "  dotnet build STK.Bridge"
  & $dotnet build (Join-Path $BridgeProject "STK.Bridge.csproj") -c Release | Out-Host
  if ($LASTEXITCODE -ne 0) { throw "STK.Bridge build failed" }
}

function Install-Bridge {
  Ensure-Dir $BridgePlugins
  $files = @("STK.Bridge.dll", "STK.Bridge.deps.json", "STK.Bridge.pdb", "config.json")
  foreach ($f in $files) {
    $src = Join-Path $BridgeOut $f
    if (-not (Test-Path $src)) { throw "Missing build artifact: $src" }
    Copy-Item $src (Join-Path $BridgePlugins $f) -Force
  }
  Write-Host "  STK.Bridge -> $BridgePlugins"
}

Write-Step "Preflight"
if (-not (Test-Path $CsgoDir)) { throw "CS2 csgo dir not found: $CsgoDir" }
Ensure-Dir (Join-Path $CsgoDir "addons")
Ensure-Dir $TempDir

Write-Step "1/5 Metamod:Source 2.0 (build 1410)"
Download-File $MetamodUrl (Join-Path $TempDir "metamod.zip")
Expand-ZipToCsgo (Join-Path $TempDir "metamod.zip")

Write-Step "2/5 CounterStrikeSharp 1.0.371 (with-runtime, Windows)"
Download-File $CssUrl (Join-Path $TempDir "css.zip")
Expand-ZipToCsgo (Join-Path $TempDir "css.zip")

Write-Step "3/5 MatchZy 0.8.15 (plugin only)"
Download-File $MatchZyUrl (Join-Path $TempDir "matchzy.zip")
Expand-ZipToCsgo (Join-Path $TempDir "matchzy.zip")

Write-Step "4/5 gameinfo.gi"
Patch-GameInfo

Write-Step "5/5 STK.Bridge"
Build-Bridge
Install-Bridge

Write-Host ""
Write-Host "INSTALL OK" -ForegroundColor Green
Write-Host "Versions: Metamod git1410 | CSS 1.0.371 | MatchZy 0.8.15 | STK.Bridge (local build)"
Write-Host ""
Write-Host "Next:"
Write-Host "  1) Restart server: start-dedicated-competitive.bat (MatchZy = competitive)"
Write-Host "  2) Console: meta list   (expect CounterStrikeSharp + plugins)"
Write-Host "  3) Edit STK.Bridge config.json WebhookSecret to match .env CS2_WEBHOOK_SECRET"
Write-Host "  4) Platform API up -> register game-server (infra/game-server/README.md)"
Write-Host ""
Write-Host "Note: STK.Bridge is skeleton — full MatchZy hooks not wired yet (TZ002)."
