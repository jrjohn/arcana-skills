# UserPromptSubmit hook (Windows) — archive lookup auto-trigger.
#
# Detects "look up something historical / identity / status" intent in the
# user's prompt, runs crs.exe vsearch behind the scenes, and injects top
# hits as additionalContext. Also sets the archive-preflight sentinel so
# subsequent raw sqlite3 / memory grep / log digging is unblocked.
#
# Failure modes (silent, never blocks):
#   - vsearch timeout / Ollama down  → silent skip, prompt unchanged
#   - trigger doesn't match           → exit 0, prompt unchanged
#   - results empty                   → don't inject, but sentinel still set
#
# This hook is a companion to archive-preflight.ps1:
#   - preflight is REACTIVE (blocks bad tool calls)
#   - this is PROACTIVE (does the right query before Claude even sees the prompt)
#
# NOTE: archive-only hook. If a separate skill (e.g. luminous) also wants
# UserPromptSubmit injection, it should ship its own .ps1 — don't bundle
# multiple unrelated triggers in one script.
#
# Installation: $env:USERPROFILE\.claude\hooks\auto-vsearch-on-prompt.ps1
# Registration: UserPromptSubmit (see install.ps1)

$ErrorActionPreference = 'SilentlyContinue'
$input_raw = [Console]::In.ReadToEnd()

try {
    $payload = $input_raw | ConvertFrom-Json
} catch {
    exit 0
}

$prompt = [string]$payload.prompt
$sid    = [string]$payload.session_id

if (-not $prompt) { exit 0 }
if ($prompt.Length -lt 4) { exit 0 }

# Archive trigger — 4 categories merged:
#   identity (.45 / 工號 / MAC / hostname / 是誰 / 誰的)
#   history  (上次 / 之前 / 歷史 / 曾經 / 以前 / 當初 / 先前 / 昨天 / 早上 / 前幾天)
#   status   (修了嗎 / 修好了 / 完成了 / 處理了 / 解了 / 搞定了 / fixed / resolved /
#             完成嗎 / 處理完 / 做完 / 還是 / 還沒 / 目前 / 現在 / 狀態)
#   question (查 / 對到 / 為何 / 為什麼 / 怎麼 / 哪個 / 哪些 / 是不是 / 有沒有 /
#             請問 / 可以嗎 / 能不能)
$ArchiveTrigger = '\.[0-9]{1,3}|工號|MAC|hostname|是誰|誰的|上次|之前|歷史|曾經|以前|當初|先前|昨天|早上|前幾天|修了嗎|修好了|完成了|處理了|解了|搞定了|fixed|resolved|完成嗎|處理完|做完|還是|還沒|目前|現在|狀態|查|對到|為何|為什麼|怎麼|哪個|哪些|是不是|有沒有|請問|可以嗎|能不能'

if ($prompt -notmatch $ArchiveTrigger) {
    exit 0
}

# Resolve crs binary: prefer %USERPROFILE%\bin\crs.exe (installer drop),
# fallback to canonical build path.
$candidates = @(
    (Join-Path $env:USERPROFILE 'bin\crs.exe'),
    (Join-Path $env:USERPROFILE 'claude-archive\crs\target\release\crs.exe')
)
$crs = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $crs) { exit 0 }

# Cross-project semantic search (vsearch is global by default).
# Bound by Claude Code's hook-level timeout (set in settings.json, typically 5s).
# vsearch typically returns in ~500ms — 1.1s; if Ollama is down it fails fast.
try {
    $result = & $crs vsearch $prompt 2>$null | Select-Object -First 8 | Out-String
} catch {
    $result = ''
}

# Set archive-preflight sentinel even if results are empty.
# Rationale: "I queried the archive, found nothing" still satisfies the
# preflight rule — subsequent sqlite3 / memory grep should now unblock.
if ($sid) {
    $sentinel = Join-Path $env:TEMP "claude-archive-preflight-$sid"
    New-Item -ItemType File -Force -Path $sentinel | Out-Null
}

if (-not $result -or $result.Trim().Length -eq 0) { exit 0 }

$ctx = @"
Auto-archive lookup (vsearch top hits, all projects):

$($result.TrimEnd())

(Auto-injected from claude-session-archive-skill. If relevant, use this context directly. If unrelated to the user's intent, ignore. Archive preflight sentinel is now set, so raw sqlite3 / memory grep / SSH log queries are unblocked for this session.)
"@

$out = @{
    hookSpecificOutput = @{
        hookEventName     = 'UserPromptSubmit'
        additionalContext = $ctx
    }
}
$out | ConvertTo-Json -Depth 5 -Compress
