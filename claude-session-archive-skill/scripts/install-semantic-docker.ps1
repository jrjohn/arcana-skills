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

  No Python required — embedding goes through crs.exe (Rust) on the host.

.NOTES
  Set OLLAMA_GPU=all environment variable before running to enable GPU
  passthrough (Linux + NVIDIA only; on Windows requires WSL2 CUDA setup).
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Archive = Join-Path $env:USERPROFILE 'claude-archive'
$Crs     = Join-Path $Archive 'crs\target\release\crs.exe'
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
if (-not (Test-Path $Crs)) {
    Write-Error "crs.exe not found at $Crs. Run install.ps1 first."
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

Write-Host "==> Pulling bge-m3..."
& docker exec $Container ollama pull bge-m3

# Convenience wrapper: ollama.ps1 → docker exec
$ollamaWrapper = Join-Path $env:USERPROFILE 'bin\ollama.ps1'
@"
& docker exec -i $Container ollama @args
"@ | Set-Content -Path $ollamaWrapper -Encoding UTF8

# Backfill via crs.exe embed-missing
$db = Join-Path $Archive 'sessions.db'
$total = [int](& sqlite3 $db 'SELECT COUNT(*) FROM msg' 2>$null)
$vec   = 0
try { $vec = [int](& sqlite3 $db 'SELECT COUNT(*) FROM msg_vec' 2>$null) } catch {}
$pending = $total - $vec

Write-Host "==> Backfill rows: $pending"
if ($pending -gt 0) {
    $logFile = Join-Path $Archive 'backfill.log'
    Write-Host "    Estimate (Docker on Win): ~$([math]::Round($pending / 120, 1)) min (~3-5x slower than native bge-m3)"
    Start-Process -FilePath $Crs -ArgumentList 'embed-missing','--workers','8' `
        -RedirectStandardOutput $logFile -WindowStyle Hidden
}

Write-Host ""
Write-Host "✓ Docker variant installed." -ForegroundColor Green
Write-Host "  Status:    docker ps --filter name=$Container"
Write-Host "  Uninstall: docker rm -f $Container; docker volume rm ollama"
