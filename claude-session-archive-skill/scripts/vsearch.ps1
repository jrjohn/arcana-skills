<#
.SYNOPSIS
  vsearch — semantic search over Claude session archive (Ollama + sqlite-vec).

.DESCRIPTION
  Thin PowerShell wrapper around `crs.exe vsearch`. Embeds query via Ollama
  (bge-m3), runs KNN over msg_vec, joins msg.

.EXAMPLE
  .\vsearch.ps1 '上次廣播 deny log 怎麼解的' network
  .\vsearch.ps1 'firewall policy adjustment'

.NOTES
  Requires (run install.ps1, then install-semantic.ps1):
    - %USERPROFILE%\bin\crs.exe
    - Ollama running (http://localhost:11434) with bge-m3 pulled
    - msg_vec table populated (crs embed-missing or built-in via crs build)
#>
param(
    [Parameter(Mandatory=$true,  Position=0)][string]$Query,
    [Parameter(Mandatory=$false, Position=1)][string]$Project = ""
)

$crs = Join-Path $env:USERPROFILE "bin\crs.exe"
if (-not (Test-Path $crs)) {
    $crs = Join-Path $env:USERPROFILE "claude-archive\crs\target\release\crs.exe"
}
if (-not (Test-Path $crs)) {
    Write-Error "crs.exe not found. Run install.ps1 first."
    exit 1
}

# Quick health check — Ollama daemon up?
try {
    $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -UseBasicParsing
} catch {
    Write-Error "Ollama daemon not reachable at localhost:11434. Run install-semantic.ps1 (or start Ollama)."
    exit 2
}

if ($Project) {
    & $crs vsearch $Query $Project
} else {
    & $crs vsearch $Query
}
