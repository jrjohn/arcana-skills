<#
.SYNOPSIS
  Optional semantic-search stack installer for Windows.

.DESCRIPTION
  Counterpart to install-semantic.sh (macOS native binary path).
  Sets up Ollama + sqlite-vec + nomic-embed-text on Windows so vsearch.ps1 works.

  What this does:
    1. Detects (or downloads) Ollama (native Windows installer or pre-installed)
    2. Pulls nomic-embed-text model (~274 MB)
    3. Creates %USERPROFILE%\claude-archive\.venv with sqlite-vec + requests
    4. Copies embed.py + vsearch.py into %USERPROFILE%\claude-archive\
    5. Kicks off backfill in background

  After install, vsearch.ps1 can be invoked from any PowerShell.

.NOTES
  Requirements:
    - Windows 10/11
    - Python 3.11+ in PATH
    - install.ps1 already run (base setup done)
    - PowerShell execution policy: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

  Docker variant: see install-semantic-docker.ps1.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$SkillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Archive  = Join-Path $env:USERPROFILE 'claude-archive'

Write-Host "==> install-semantic.ps1" -ForegroundColor Cyan

if (-not (Test-Path $Archive)) {
    Write-Error "Run install.ps1 first — base setup not detected at $Archive"
}

# 1. Ollama
$ollamaInstalled = $null -ne (Get-Command ollama -ErrorAction SilentlyContinue)
if (-not $ollamaInstalled) {
    Write-Host "==> Ollama not in PATH. Downloading official Windows installer..."
    $url = 'https://ollama.com/download/OllamaSetup.exe'
    $exe = Join-Path $env:TEMP 'OllamaSetup.exe'
    Invoke-WebRequest -Uri $url -OutFile $exe -UseBasicParsing
    Write-Host "    Launching installer (will need user click-through)..."
    Start-Process -FilePath $exe -Wait
    Remove-Item $exe -Force
    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        Write-Error "Ollama install did not complete. Re-run after manual install."
    }
}
Write-Host "    ollama: $((& ollama --version) | Select-Object -First 1)"

# 2. wait for ollama daemon (Windows installer auto-starts it)
Write-Host "==> Waiting for Ollama daemon at localhost:11434 ..."
$retries = 10
while ($retries -gt 0) {
    try {
        $null = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 2 -UseBasicParsing
        Write-Host "    daemon ready"
        break
    } catch {
        Start-Sleep -Seconds 2
        $retries--
    }
}
if ($retries -eq 0) { Write-Error "Ollama daemon not reachable. Start it manually." }

# 3. pull model
$models = & ollama list 2>$null
if ($models -notmatch 'nomic-embed-text') {
    Write-Host "==> Pulling nomic-embed-text (~274 MB)..."
    & ollama pull nomic-embed-text
}
Write-Host "    model ready: nomic-embed-text"

# 4. python venv
$venv = Join-Path $Archive '.venv'
if (-not (Test-Path "$venv\Scripts\python.exe")) {
    Write-Host "==> Creating venv at $venv"
    & python -m venv $venv
}
$venvPython = Join-Path $venv 'Scripts\python.exe'
$venvPip    = Join-Path $venv 'Scripts\pip.exe'

Write-Host "==> Installing python deps..."
& $venvPip install --quiet --upgrade pip
& $venvPip install --quiet sqlite-vec requests
$svcVer = & $venvPython -c "import sqlite_vec; print(sqlite_vec.__version__)" 2>&1
Write-Host "    sqlite-vec: $svcVer"

# 5. copy scripts
Write-Host "==> Installing embed.py + vsearch.py..."
Copy-Item -Force (Join-Path $SkillDir 'scripts\embed.py')   (Join-Path $Archive 'embed.py')
Copy-Item -Force (Join-Path $SkillDir 'scripts\vsearch.py') (Join-Path $Archive 'vsearch.py')

# 6. ensure newer build.py (with maybe_embed_new hook)
Copy-Item -Force (Join-Path $SkillDir 'scripts\build.py') (Join-Path $Archive 'build.py')

# 7. kick off backfill in background
$pendingQuery = @"
import sqlite3, sqlite_vec
c = sqlite3.connect(r'$Archive\sessions.db')
c.enable_load_extension(True); sqlite_vec.load(c)
c.execute('CREATE VIRTUAL TABLE IF NOT EXISTS msg_vec USING vec0(embedding float[768] distance_metric=cosine)')
total = c.execute('SELECT COUNT(*) FROM msg').fetchone()[0]
try:
    vec = c.execute('SELECT COUNT(*) FROM msg_vec').fetchone()[0]
except Exception:
    vec = 0
print(total - vec)
"@
$pending = & $venvPython -c $pendingQuery
$pending = [int]$pending

Write-Host "==> Rows to backfill: $pending"
if ($pending -gt 0) {
    $logFile = Join-Path $Archive 'backfill.log'
    Write-Host "==> Launching backfill in background"
    Write-Host "    Log: $logFile"
    Write-Host "    Estimate: ~$([math]::Round($pending / 1800, 1)) min on Apple Silicon-equivalent CPU"
    Start-Process -FilePath $venvPython -ArgumentList "`"$Archive\embed.py`"" `
        -RedirectStandardOutput $logFile -WindowStyle Hidden
}

Write-Host ""
Write-Host "✓ Semantic stack installed." -ForegroundColor Green
Write-Host "  Once backfill finishes:"
Write-Host "    vsearch.ps1 '上次廣播 deny log 怎麼解的'"
Write-Host "    vsearch.ps1 'wireless ap reboot issue' network"
