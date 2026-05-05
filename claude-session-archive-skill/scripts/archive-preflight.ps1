# PreToolUse hook (Bash + Read) — enforce vsearch / csearch preflight before:
#   (a) raw sqlite3 against the archive DB, or
#   (b) Select-String / Get-Content / sls / cat / head / tail on a memory
#       file in $env:USERPROFILE\.claude\projects\*\memory\*.md, or
#   (c) Read tool reading the same memory files.
#
# See archive-preflight.sh for the rationale; PowerShell port for Windows.
#
# Sentinel: $env:TEMP\claude-archive-preflight-<session_id>
#
# Installation: $env:USERPROFILE\.claude\hooks\archive-preflight.ps1
# Registration: PreToolUse matchers Bash + Read (see install.ps1)

$ErrorActionPreference = 'SilentlyContinue'
$input_raw = [Console]::In.ReadToEnd()

try {
    $payload = $input_raw | ConvertFrom-Json
} catch {
    exit 0
}

$session_id = $payload.session_id
$tool_name  = $payload.tool_name
$command    = if ($payload.tool_input.command)   { [string]$payload.tool_input.command }   else { '' }
$file_path  = if ($payload.tool_input.file_path) { [string]$payload.tool_input.file_path } else { '' }

if (-not $session_id) { exit 0 }

$sentinel = Join-Path $env:TEMP "claude-archive-preflight-$session_id"

# Memory-dir regex: ~/.claude/projects/<project-slug>/memory/<file>.md
$mem_re = '\.claude[\\/]projects[\\/][^\\/]+[\\/]memory[\\/][^\\/]+\.md'

function Deny([string]$reason) {
    $obj = @{
        hookSpecificOutput = @{
            hookEventName            = 'PreToolUse'
            permissionDecision       = 'deny'
            permissionDecisionReason = $reason
        }
    }
    $obj | ConvertTo-Json -Depth 5 -Compress
    exit 0
}

# 1. vsearch / csearch invocation -> mark preflight done
if ($command -match '(^|[^A-Za-z0-9_])(vsearch|csearch)([^A-Za-z0-9_]|$)') {
    New-Item -ItemType File -Force -Path $sentinel | Out-Null
    exit 0
}

# 2. raw sqlite3 against archive DB
if ($command -match 'sqlite3(\s|$).*(sessions\.db|claude-archive)') {
    if (Test-Path $sentinel) { exit 0 }
    Deny "Preflight rule: run vsearch first (csearch for exact IP/hostname/filename) before raw sqlite3 against the archive DB. Invoke vsearch or csearch in this session — it sets a sentinel and unblocks subsequent SQL queries."
}

# 3. Bash/PS grep on memory file
if ($command -match '(^|[^A-Za-z0-9_])(grep|sls|Select-String|Get-Content|cat|gc|head|tail|less|more|sed|awk)([^A-Za-z0-9_]|$).*' + $mem_re) {
    if (Test-Path $sentinel) { exit 0 }
    Deny "Memory file is a stale INDEX, not source of truth. For roster / device / credential / history queries, run vsearch first (default) or csearch (known phrase / IP / identifier). Memory grep is allowed only after vsearch/csearch unlocks the sentinel — or for 'recent context I just discussed this session' lookups."
}

# 4. Read tool on memory file
if ($tool_name -eq 'Read' -and $file_path -match $mem_re) {
    if (Test-Path $sentinel) { exit 0 }
    # Allow MEMORY.md (the index file itself)
    if ($file_path -match '[\\/]MEMORY\.md$') { exit 0 }
    Deny "Memory file is a stale INDEX, not source of truth. For roster / device / credential / history queries, run vsearch first (default) or csearch (known phrase / IP / identifier). Read on memory/*.md is allowed only after vsearch/csearch unlocks the sentinel — or for 'recent context I just discussed this session' lookups."
}

exit 0
