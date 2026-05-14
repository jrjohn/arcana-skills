# PreToolUse hook (Bash + Read) — enforce vsearch / csearch preflight before:
#   (a) raw sqlite3 SEARCH (LIKE / MATCH / msg_fts / GLOB) — HARD DENY regardless of sentinel,
#   (b) raw sqlite3 metadata against archive DB — allow only if sentinel valid,
#   (c) Select-String / Get-Content / sls / cat / head / tail / sed / awk on a
#       memory file in $env:USERPROFILE\.claude\projects\*\memory\*.md,
#   (d) Read tool reading the same memory files,
#   (e) ssh ... grep|tail|cat ... /var/log/* (investigative remote log
#       queries — prior session may already have extracted the answer),
#   (f) local grep|cat|tail on /var/log/ or *.log files (same logic as remote),
#   (g) git log --grep / -S (investigative git history search).
#
# Why memory enforcement: memory files are stale, hand-curated indexes
# (incomplete by design). For roster / device / credential / history
# queries, the canonical source is the archive DB. csearch/vsearch return
# the actual past conversation transcript verbatim; memory grep returns
# only what someone manually wrote down.
#
# Why log enforcement: investigative log digs (SSH or local) often duplicate
# work already done in a prior session. The archive captures every prior
# Bash tool_use + tool_result verbatim — it's faster to vsearch first and
# reuse than to re-SSH and re-grep.
#
# Why sqlite3 SEARCH forbidden (v1.11+): raw LIKE / MATCH / msg_fts / GLOB
# against sessions.db is hard-blocked regardless of sentinel — csearch is
# faster (FTS5 vs LIKE), supports phrase/boolean syntax, and returns ~258
# chars per hit which covers 99% of credential/history/context lookups.
# Forcing csearch keeps archive-access discipline post-compact when the
# model has lost procedural memory but the sentinel is still warm. Metadata
# queries (COUNT / PRAGMA / .schema / msg_vec maintenance) are still
# allowed when the sentinel is valid.
#
# Why sentinel TTL (v1.11+): post-compact, the model loses procedural
# memory of having run vsearch but the session_id (and thus sentinel)
# persists. Without a TTL, the hook would allow sqlite3 forever based on
# a vsearch that ran 4 hours ago. 30-min TTL forces re-vsearch after any
# meaningful idle gap. auto-vsearch-on-prompt.ps1 refreshes the sentinel
# on every prompt that matches archive-intent keywords, so active
# conversations rarely hit the TTL.
#
# Behavior:
#   - vsearch / csearch invocation     -> refresh sentinel, allow.
#   - sqlite3 SEARCH (LIKE/MATCH/...)  -> ALWAYS deny (sentinel irrelevant).
#   - sqlite3 metadata against DB      -> allow only if sentinel valid (fresh).
#   - grep/cat/.../Read on memory     -> allow only if sentinel valid.
#   - Read on MEMORY.md (the index)    -> always allow (auto-loaded by system).
#   - ssh + log investigation          -> allow only if sentinel valid.
#   - local log grep                   -> allow only if sentinel valid.
#   - git log --grep / -S              -> allow only if sentinel valid.
#   - Otherwise: allow silently.
#
# Sentinel: $env:TEMP\claude-archive-preflight-<session_id>  (TTL 30 min)
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

# Sentinel TTL: 30 minutes. See header for rationale (compact gap).
$SentinelTtlSec = 1800

# Memory-dir regex: ~/.claude/projects/<project-slug>/memory/<file>.md
# Matches both Windows backslash and forward slash (cross-platform path repr).
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

# Check sentinel exists AND is fresh (within TTL). Expired = likely compact gap.
function Test-SentinelValid {
    if (-not (Test-Path $sentinel)) { return $false }
    try {
        $mtime = (Get-Item -LiteralPath $sentinel).LastWriteTime
        $age   = ((Get-Date) - $mtime).TotalSeconds
        if ($age -gt $SentinelTtlSec) {
            Remove-Item -LiteralPath $sentinel -Force -ErrorAction SilentlyContinue
            return $false
        }
        return $true
    } catch {
        return $false
    }
}

# 1. vsearch / csearch invocation -> refresh sentinel (reset mtime to now)
if ($command -match '(^|[^A-Za-z0-9_])(vsearch|csearch)([^A-Za-z0-9_]|$)') {
    New-Item -ItemType File -Force -Path $sentinel | Out-Null
    exit 0
}

# 2. raw sqlite3 against the archive DB
#    - SEARCH patterns (LIKE / MATCH / msg_fts / GLOB) -> HARD DENY regardless of sentinel
#    - METADATA queries (COUNT / PRAGMA / .schema / msg_vec maintenance)
#      -> allowed only if sentinel valid (preflight discipline still required)
if ($command -match 'sqlite3(\s|$).*(sessions\.db|claude-archive)') {
    # Search-style query -> hard deny (sentinel doesn't help here)
    if ($command -imatch '(LIKE\s|MATCH\s|msg_fts|GLOB\s)') {
        Deny 'Raw sqlite3 SEARCH against sessions.db is forbidden — use csearch (FTS5) or vsearch (semantic) instead. Reasons: (a) csearch already returns ts + project + role + 258 chars per hit, covers credential / history / context lookups, (b) sqlite3 LIKE is slower than FTS5 MATCH, (c) forcing csearch keeps archive-access discipline post-compact. csearch syntax: phrase ""..."", boolean AND/OR/NOT, --limit N (default 20). For deeper drill-down, extend csearch tooling, not raw SQL.'
    }
    # Metadata / schema queries -> allow only if sentinel valid
    if (Test-SentinelValid) { exit 0 }
    Deny 'Even metadata sqlite3 against sessions.db requires preflight — run vsearch or csearch first to confirm intent and unlock sentinel. (Sentinel may have expired after 30 min — post-compact gap; re-running vsearch refreshes it.)'
}

# 3. Bash/PS grep / cat / head / tail / Select-String / Get-Content / sed / awk on memory file
if ($command -match ('(^|[^A-Za-z0-9_])(grep|sls|Select-String|Get-Content|cat|gc|head|tail|less|more|sed|awk)([^A-Za-z0-9_]|$).*' + $mem_re)) {
    if (Test-SentinelValid) { exit 0 }
    Deny "Memory file is a stale INDEX, not source of truth. For roster / device / credential / history queries, run vsearch first (default) or csearch (known phrase / IP / identifier). Memory grep is allowed only after vsearch/csearch unlocks the sentinel — or for 'recent context I just discussed this session' lookups."
}

# 4. Read tool on memory file
if ($tool_name -eq 'Read' -and $file_path -match $mem_re) {
    if (Test-SentinelValid) { exit 0 }
    # Allow MEMORY.md (the index file itself) — auto-loaded by system anyway
    if ($file_path -match '[\\/]MEMORY\.md$') { exit 0 }
    Deny "Memory file is a stale INDEX, not source of truth. For roster / device / credential / history queries, run vsearch first (default) or csearch (known phrase / IP / identifier). Read on memory/*.md is allowed only after vsearch/csearch unlocks the sentinel — or for 'recent context I just discussed this session' lookups."
}

# 5. SSH command containing investigative log-grep pattern
#    (e.g. "ssh ... grep ... /var/log/...", "ssh nas tail -f log").
#    Intent is "look up something in remote logs" — archive may already have it.
if ($command -match 'ssh\s' -and `
    $command -match '(grep|cat|tail|head|less|sed|awk|find|sls|Select-String|Get-Content)\s' -and `
    $command -match '(/var/log/|\.log[\s"''|]|\.log\.gz)') {
    if (Test-SentinelValid) { exit 0 }
    Deny "About to SSH and grep/cat/tail a log file. Investigative work like this often duplicates a prior session — vsearch first to see if the answer is already in the archive. If it's genuinely a new investigation, vsearch returns 0 results and still sets the sentinel, which then unlocks subsequent SSH log queries."
}

# 6. Local grep/cat/tail on /var/log/* or *.log
if ($command -match '(^|[^A-Za-z0-9_])(grep|sls|Select-String|Get-Content|cat|gc|tail|head|less|sed|awk)([^A-Za-z0-9_]|$)[^|]*(/var/log/|\.log[\s"''|]|\.log\.gz)') {
    if (Test-SentinelValid) { exit 0 }
    Deny "About to grep/cat a log file locally. Same logic as remote SSH log queries — vsearch first to see if a prior session already extracted this. If genuinely new, vsearch returns 0 and the sentinel still unlocks."
}

# 7. git log --grep / -S (investigative git history search)
if ($command -match 'git\s+log\s' -and `
    $command -match '(--grep[=\s]|--all-match|-S[\s"''])') {
    if (Test-SentinelValid) { exit 0 }
    Deny "git log --grep / -S is investigative — same logic as log file grep. vsearch first; if genuinely new investigation the sentinel still unlocks after."
}

exit 0
