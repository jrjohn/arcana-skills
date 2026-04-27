<#
.SYNOPSIS
  Docker variant of install-semantic.ps1 for Windows.

.DESCRIPTION
  Run if you already have Docker Desktop on Windows. Runs Ollama in a container
  instead of native Windows binary.

  Trade-offs vs native install-semantic.ps1:
    + Cleaner uninstall (one container + one volume)
    + Same command path on macOS/Linux/Windows
    - Docker Desktop on Windows uses WSL2 backend → slightly more memory overhead
    - No GPU passthrough unless WSL2-CUDA configured (~3-5x slower vs native)

.NOTES
  Set OLLAMA_GPU=all environment variable before running to enable GPU
  passthrough (Linux + NVIDIA only; on Windows requires WSL2 CUDA setup).
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$SkillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Archive  = Join-Path $env:USERPROFILE 'claude-archive'
$Container = 'claude-archive-ollama'
$Image     = 'ollama/ollama:latest'

Write-Host "==> install-semantic-docker.ps1" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Install Docker Desktop first, or use install-semantic.ps1."
}
try { & docker info > $null } catch { Write-Error "Docker daemon not running." }

if (-not (Test-Path $Archive)) {
    Write-Error "Run install.ps1 first — base setup not detected at $Archive"
}

Write-Host "==> Pulling $Image (~1 GB)..."
& docker pull $Image

# Idempotent: remove stale container if any
$exists = (& docker ps -a --filter "name=$Container" --format '{{.Names}}') -eq $Container
if ($exists) {
    Write-Host "==> Removing existing container $Container"
    & docker rm -f $Container | Out-Null
}

$gpuFlag = @()
if ($env:OLLAMA_GPU -eq 'all') { $gpuFlag = @('--gpus','all') }

Write-Host "==> Starting container..."
& docker run -d `
    --name $Container `
    --restart unless-stopped `
    -p 127.0.0.1:11434:11434 `
    -v ollama:/root/.ollama `
    -e OLLAMA_KEEP_ALIVE=30m `
    @gpuFlag `
    $Image | Out-Null

Write-Host "==> Waiting for daemon..."
$retries = 10
while ($retries -gt 0) {
    try { $null = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 2 -UseBasicParsing; break }
    catch { Start-Sleep -Seconds 2; $retries-- }
}
if ($retries -eq 0) { Write-Error "Daemon not ready" }
Write-Host "    daemon ready"

Write-Host "==> Pulling nomic-embed-text..."
& docker exec $Container ollama pull nomic-embed-text

# Python venv + scripts (same as native variant)
$venv = Join-Path $Archive '.venv'
if (-not (Test-Path "$venv\Scripts\python.exe")) {
    & python -m venv $venv
}
$venvPython = Join-Path $venv 'Scripts\python.exe'
$venvPip    = Join-Path $venv 'Scripts\pip.exe'
& $venvPip install --quiet --upgrade pip
& $venvPip install --quiet sqlite-vec requests

Copy-Item -Force (Join-Path $SkillDir 'scripts\embed.py')   (Join-Path $Archive 'embed.py')
Copy-Item -Force (Join-Path $SkillDir 'scripts\vsearch.py') (Join-Path $Archive 'vsearch.py')
Copy-Item -Force (Join-Path $SkillDir 'scripts\build.py')   (Join-Path $Archive 'build.py')

# convenience wrapper: ollama.ps1 → docker exec
$ollamaWrapper = Join-Path $env:USERPROFILE 'bin\ollama.ps1'
@"
& docker exec -i $Container ollama @args
"@ | Set-Content -Path $ollamaWrapper -Encoding UTF8

# Backfill
$pendingQuery = @"
import sqlite3, sqlite_vec
c = sqlite3.connect(r'$Archive\sessions.db')
c.enable_load_extension(True); sqlite_vec.load(c)
c.execute('CREATE VIRTUAL TABLE IF NOT EXISTS msg_vec USING vec0(embedding float[768] distance_metric=cosine)')
total = c.execute('SELECT COUNT(*) FROM msg').fetchone()[0]
try: vec = c.execute('SELECT COUNT(*) FROM msg_vec').fetchone()[0]
except Exception: vec = 0
print(total - vec)
"@
$pending = [int](& $venvPython -c $pendingQuery)

Write-Host "==> Backfill rows: $pending"
if ($pending -gt 0) {
    $logFile = Join-Path $Archive 'backfill.log'
    Write-Host "    Estimate (Docker on Win): ~$([math]::Round($pending / 600, 1)) min (~3-5x slower than native)"
    Start-Process -FilePath $venvPython -ArgumentList "`"$Archive\embed.py`"" `
        -RedirectStandardOutput $logFile -WindowStyle Hidden
}

Write-Host ""
Write-Host "✓ Docker variant installed." -ForegroundColor Green
Write-Host "  Status:    docker ps --filter name=$Container"
Write-Host "  Uninstall: docker rm -f $Container; docker volume rm ollama"
