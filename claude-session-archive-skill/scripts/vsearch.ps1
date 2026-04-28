<#
.SYNOPSIS
  vsearch — semantic search over Claude session archive (Ollama + sqlite-vec).

.DESCRIPTION
  Windows PowerShell counterpart to scripts/vsearch (bash).
  Embeds query via Ollama (bge-m3), runs KNN over msg_vec, joins msg.

.EXAMPLE
  .\vsearch.ps1 '上次廣播 deny log 怎麼解的' network
  .\vsearch.ps1 'firewall policy adjustment'

.NOTES
  Requires (run install-semantic.ps1 first):
    - Ollama running (http://localhost:11434) with bge-m3 pulled
    - %USERPROFILE%\claude-archive\.venv with sqlite-vec + requests installed
    - %USERPROFILE%\claude-archive\vsearch.py + embed.py
#>
param(
    [Parameter(Mandatory=$true,  Position=0)][string]$Query,
    [Parameter(Mandatory=$false, Position=1)][string]$Project = ""
)

$venvPython = Join-Path $env:USERPROFILE "claude-archive\.venv\Scripts\python.exe"
$vsearchPy  = Join-Path $env:USERPROFILE "claude-archive\vsearch.py"

if (-not (Test-Path $venvPython)) {
    Write-Error "venv not found at $venvPython. Run install-semantic.ps1 first."
    exit 1
}
if (-not (Test-Path $vsearchPy)) {
    Write-Error "$vsearchPy missing. Run install-semantic.ps1 first."
    exit 1
}

# Quick health check — Ollama daemon up?
try {
    $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -UseBasicParsing
} catch {
    Write-Error "Ollama daemon not reachable at localhost:11434. Start it (or run install-semantic.ps1)."
    exit 2
}

if ($Project) {
    & $venvPython $vsearchPy $Query $Project
} else {
    & $venvPython $vsearchPy $Query
}
