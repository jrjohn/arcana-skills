<#
.SYNOPSIS
  Add Ollama + bge-m3 semantic stack on Windows.

.DESCRIPTION
  Counterpart to install-semantic.sh (macOS native binary path).
  Run AFTER install.ps1 (base setup) is complete.

  What this does:
    1. Detects (or downloads) Ollama (native Windows installer)
    2. Pulls bge-m3 model (~1.2 GB)
    3. Kicks off backfill in background via `crs.exe embed-missing`

  No Python required — embedding goes through crs.exe (Rust). After install,
  vsearch.ps1 / `crs vsearch` work over the same msg_vec table.

.NOTES
  Requirements:
    - Windows 10/11
    - install.ps1 already run (base setup done — crs.exe + DB)
    - PowerShell execution policy: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

  Docker variant: see install-semantic-docker.ps1.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Archive = Join-Path $env:USERPROFILE 'claude-archive'
$Crs     = Join-Path $Archive 'crs\target\release\crs.exe'

Write-Host "==> install-semantic.ps1" -ForegroundColor Cyan

if (-not (Test-Path $Archive)) {
    Write-Error "Run install.ps1 first — base setup not detected at $Archive"
}
if (-not (Test-Path $Crs)) {
    Write-Error "crs.exe not found at $Crs. Run install.ps1 first."
}
Write-Host "    crs: $Crs"

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
if ($models -notmatch 'bge-m3') {
    Write-Host "==> Pulling bge-m3 (~1.2 GB)..."
    & ollama pull bge-m3
}
Write-Host "    model ready: bge-m3"

# 4. kick off backfill in background via crs.exe embed-missing
$db = Join-Path $Archive 'sessions.db'
$total = [int](& sqlite3 $db 'SELECT COUNT(*) FROM msg' 2>$null)
$vec   = 0
try { $vec = [int](& sqlite3 $db 'SELECT COUNT(*) FROM msg_vec' 2>$null) } catch {}
$pending = $total - $vec

Write-Host "==> Rows to backfill: $pending"
if ($pending -gt 0) {
    $logFile = Join-Path $Archive 'backfill.log'
    Write-Host "==> Launching parallel backfill in background (8 workers)"
    Write-Host "    Log: $logFile"
    Write-Host "    Estimate: ~$([math]::Round($pending / 420, 1)) min (bge-m3 ~7 emb/sec @ 8 workers)"
    Start-Process -FilePath $Crs -ArgumentList 'embed-missing','--workers','8' `
        -RedirectStandardOutput $logFile -WindowStyle Hidden
}

Write-Host ""
Write-Host "✓ Semantic stack installed." -ForegroundColor Green
Write-Host "  Once backfill finishes:"
Write-Host "    vsearch.ps1 '上次廣播 deny log 怎麼解的'"
Write-Host "    crs vsearch 'wireless ap reboot issue' network"
