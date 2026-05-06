#!/usr/bin/env bash
# UserPromptSubmit hook — archive lookup auto-trigger.
#
# Detects "look up something historical / identity / status" intent in the
# user's prompt, runs vsearch behind the scenes, and injects top hits as
# additionalContext. Also sets the archive-preflight sentinel so subsequent
# raw sqlite3 / memory grep / log digging is unblocked.
#
# Why: most "who is .45?" / "what was the password for X?" / "did we fix Y?"
# style questions are already answered verbatim in the archive DB. Running
# vsearch on prompt submit avoids the round-trip of Claude having to remember
# the rule, query the archive, then answer. The injected context lands in
# Claude's first turn so the model can answer immediately.
#
# Failure modes (silent, never blocks):
#   - vsearch timeout / Ollama down  → silent skip, prompt unchanged
#   - trigger doesn't match           → exit 0, prompt unchanged
#   - results empty                   → don't inject, but sentinel still set
#                                       (we did query, just got nothing)
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

# Cross-project semantic search (vsearch is global by default).
# macOS lacks `timeout`/`gtimeout` by default; rely on Claude Code's
# hook-level timeout (set in settings.json, typically 5s) to bound runtime.
# vsearch typically returns in 500ms; if Ollama is down it fails fast.
result=$("$CRS" vsearch "$prompt" 2>/dev/null | head -8)

# Set archive-preflight sentinel even if results are empty.
# Rationale: "I queried the archive, found nothing" still satisfies the
# preflight rule — subsequent SSH / sqlite3 / memory grep should now unblock.
[ -n "$sid" ] && : > "/tmp/claude-archive-preflight-${sid}"

# Empty results → don't inject (avoid noise) but sentinel is set.
[ -z "$result" ] && exit 0

ctx="Auto-archive lookup (vsearch top hits, all projects):

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
