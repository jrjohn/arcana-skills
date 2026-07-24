#!/usr/bin/env bash
# UserPromptSubmit hook — archive lookup auto-trigger.
#
# Detects "look up something historical / identity / status" intent in the
# user's prompt, runs osearch behind the scenes, and injects top hits as
# additionalContext. Also sets the archive-preflight sentinel so subsequent
# raw sqlite3 / memory grep / log digging is unblocked.
#
# osearch is the default front door (orient→recall→pin RRF fusion; unions the
# vsearch + csearch legs). On a sqlite-only backend, or before the distill/orient
# layer is populated, osearch ≈ vsearch (RRF guarantees osearch >= vsearch), so it
# is always a safe default. (Filename kept as-is to avoid churning install refs.)
#
# Why: most "who is .45?" / "what was the password for X?" / "did we fix Y?"
# style questions are already answered verbatim in the archive DB. Running
# osearch on prompt submit avoids the round-trip of Claude having to remember
# the rule, query the archive, then answer. The injected context lands in
# Claude's first turn so the model can answer immediately.
#
# Failure modes (silent, never blocks):
#   - search slow/down (e.g. remote PG over WAN) → hard-capped + skipped, unchanged
#   - trigger doesn't match                       → exit 0, prompt unchanged
#   - results empty                               → don't inject, but sentinel still set
#                                                   (we did query, just got nothing)
#
# This hook is a *companion* to archive-preflight.sh:
#   - preflight is REACTIVE (blocks bad tool calls)
#   - this is PROACTIVE (does the right query before Claude even sees the prompt)
#
# NOTE: this is an archive-only hook. If a separate skill (e.g. luminous)
# also wants UserPromptSubmit injection, it should ship its own hook —
# don't bundle multiple unrelated triggers in one script.

set -uo pipefail

input=$(cat)
prompt=$(printf '%s' "$input" | jq -r '.prompt // empty')
sid=$(printf '%s' "$input" | jq -r '.session_id // empty')

[ -z "$prompt" ] && exit 0
[ ${#prompt} -lt 4 ] && exit 0

# Archive trigger — 4 categories merged:
#   identity (.45 / 工號 / MAC / hostname / 是誰 / 誰的)
#   history  (上次 / 之前 / 歷史 / 曾經 / 以前 / 當初 / 先前 / 昨天 / 早上 / 前幾天)
#   status   (修了嗎 / 修好了 / 完成了 / 處理了 / 解了 / 搞定了 / fixed / resolved /
#             完成嗎 / 處理完 / 做完 / 還是 / 還沒 / 目前 / 現在 / 狀態)
#   question (查 / 對到 / 為何 / 為什麼 / 怎麼 / 哪個 / 哪些 / 是不是 / 有沒有 /
#             請問 / 可以嗎 / 能不能)
ARCHIVE_TRIGGER='\.[0-9]{1,3}|工號|MAC|hostname|是誰|誰的|上次|之前|歷史|曾經|以前|當初|先前|昨天|早上|前幾天|修了嗎|修好了|完成了|處理了|解了|搞定了|fixed|resolved|完成嗎|處理完|做完|還是|還沒|目前|現在|狀態|查|對到|為何|為什麼|怎麼|哪個|哪些|是不是|有沒有|請問|可以嗎|能不能'

if ! printf '%s' "$prompt" | grep -qE "$ARCHIVE_TRIGGER"; then
    exit 0
fi

# Resolve crs binary: prefer ~/bin/crs (symlink installed by install.sh),
# fallback to canonical build path.
if [ -x "$HOME/bin/crs" ]; then
    CRS="$HOME/bin/crs"
elif [ -x "$HOME/claude-archive/crs/target/release/crs" ]; then
    CRS="$HOME/claude-archive/crs/target/release/crs"
else
    # crs not installed — silently skip
    exit 0
fi

# Set archive-preflight sentinel for this archive-intent prompt, even if the
# search is skipped (cooldown) or returns nothing — we "consulted" the archive,
# so subsequent SSH / sqlite3 / memory grep should now unblock.
[ -n "$sid" ] && : > "/tmp/claude-archive-preflight-${sid}"

# Cross-project search via osearch (global by default). osearch warm ~1-2s, but a
# slow/unreachable remote PG (e.g. over WAN) can hang 20-30s and blow past the
# hook's settings.json timeout, erroring every prompt. Two guards:
#   (a) hard cap on runtime — prefer `timeout`/`gtimeout` (Linux/coreutils), else
#       `perl` alarm (survives exec; macOS has perl), else a bare call. A run
#       killed by the cap exits >=124, which we detect.
#   (b) circuit breaker — after a timeout, skip the search for COOLDOWN_SECS so a
#       degraded backend doesn't make every prompt wait. Auto-recovers when healthy.
COOLDOWN="/tmp/claude-osearch-cooldown"
SEARCH_TIMEOUT=4
COOLDOWN_SECS=180

if [ -f "$COOLDOWN" ]; then
    mtime=$(stat -f %m "$COOLDOWN" 2>/dev/null || stat -c %Y "$COOLDOWN" 2>/dev/null || echo 0)
    [ "$(( $(date +%s) - mtime ))" -lt "$COOLDOWN_SECS" ] && exit 0
    rm -f "$COOLDOWN"
fi

if command -v timeout >/dev/null 2>&1; then
    result=$(timeout "$SEARCH_TIMEOUT" "$CRS" osearch "$prompt" 2>/dev/null); rc=$?
elif command -v gtimeout >/dev/null 2>&1; then
    result=$(gtimeout "$SEARCH_TIMEOUT" "$CRS" osearch "$prompt" 2>/dev/null); rc=$?
elif command -v perl >/dev/null 2>&1; then
    result=$(perl -e 'alarm shift; exec @ARGV' "$SEARCH_TIMEOUT" "$CRS" osearch "$prompt" 2>/dev/null); rc=$?
else
    result=$("$CRS" osearch "$prompt" 2>/dev/null); rc=$?
fi

# Timed out (cap killed it) → arm breaker, skip this turn.
[ "$rc" -ge 124 ] && { : > "$COOLDOWN"; exit 0; }
rm -f "$COOLDOWN"
result=$(printf '%s' "$result" | head -8)

# Empty results → don't inject (avoid noise) but sentinel is set.
[ -z "$result" ] && exit 0

ctx="Auto-archive lookup (osearch top hits, all projects):

$result

(Auto-injected from claude-session-archive-skill. If relevant, use this context directly. If unrelated to the user's intent, ignore. Archive preflight sentinel is now set, so raw sqlite3 / memory grep / SSH log queries are unblocked for this session.)"

# Encode to JSON safely (jq is already a dependency for the archive skill)
ctx_json=$(printf '%s' "$ctx" | jq -Rs .)

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": $ctx_json
  }
}
EOF
