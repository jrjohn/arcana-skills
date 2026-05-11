#!/usr/bin/env bash
# PreToolUse hook (Bash + Read) — enforce vsearch / csearch preflight before:
#   (a) raw sqlite3 against ~/claude-archive/sessions.db, or
#   (b) grep / cat / head / tail / less / more / sed / awk on a memory file
#       in ~/.claude/projects/*/memory/*.md, or
#   (c) Read tool reading the same memory files, or
#   (d) ssh ... grep|tail|cat ... /var/log/* (investigative remote log
#       queries — prior session may already have extracted the answer), or
#   (e) local grep|cat|tail on /var/log/ or *.log files (same logic as remote), or
#   (f) git log --grep / -S (investigative git history search).
#
# Why memory enforcement: memory files are stale, hand-curated indexes
# (incomplete by design). For roster / device / credential / history
# queries, the canonical source is the archive DB. csearch/vsearch return
# the actual past conversation transcript verbatim; memory grep returns
# only what someone manually wrote down. Forcing vsearch/csearch first
# prevents the "I'll just grep memory and miss half the data" antipattern.
#
# Why log enforcement: investigative log digs (SSH or local) often duplicate
# work already done in a prior session. The archive captures every prior
# Bash tool_use + tool_result verbatim — it's faster to vsearch first and
# reuse than to re-SSH and re-grep. If the answer genuinely isn't in the
# archive, vsearch returns 0 results and the sentinel still unlocks.
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
# meaningful idle gap. auto-vsearch-on-prompt.sh refreshes the sentinel
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
# Sentinel: /tmp/claude-archive-preflight-<session_id>  (TTL 30 min)
#
# Installation: ~/.claude/hooks/archive-preflight.sh
# Registration: PreToolUse matchers Bash + Read (see install.sh)

set -uo pipefail

input=$(cat)

session_id=$(printf '%s' "$input" | jq -r '.session_id // empty')
tool_name=$(printf '%s' "$input" | jq -r '.tool_name // empty')
command=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')

[ -z "$session_id" ] && exit 0

sentinel="/tmp/claude-archive-preflight-${session_id}"

# Sentinel TTL: 30 minutes. See header for rationale (compact gap).
SENTINEL_TTL_SEC=1800

# Memory-dir regex: ~/.claude/projects/<project-slug>/memory/<file>.md
mem_dir_re='\.claude/projects/[^/]+/memory/[^/]+\.md'

deny_with_reason() {
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "$1"
  }
}
EOF
    exit 0
}

# Check sentinel exists AND is fresh (within TTL). Expired = likely compact gap.
sentinel_valid() {
    [ -e "$sentinel" ] || return 1
    local mtime now age
    # macOS stat -f, Linux stat -c
    mtime=$(stat -f %m "$sentinel" 2>/dev/null || stat -c %Y "$sentinel" 2>/dev/null || echo 0)
    now=$(date +%s)
    age=$(( now - mtime ))
    if [ "$age" -gt "$SENTINEL_TTL_SEC" ]; then
        rm -f "$sentinel"
        return 1
    fi
    return 0
}

# 1. vsearch / csearch invocation -> refresh sentinel (sets mtime to now)
if [ -n "$command" ] && printf '%s' "$command" | grep -qE '(^|[^A-Za-z0-9_])(vsearch|csearch)([^A-Za-z0-9_]|$)'; then
    : > "$sentinel"
    exit 0
fi

# 2. raw sqlite3 against the archive DB
#    - SEARCH patterns (LIKE / MATCH / msg_fts / GLOB) -> HARD DENY regardless of sentinel
#    - METADATA queries (COUNT / PRAGMA / .schema / sqlite_master / msg_vec maintenance)
#      -> allowed only if sentinel valid (preflight discipline still required)
if [ -n "$command" ] && printf '%s' "$command" | grep -qE 'sqlite3([[:space:]]|$).*(sessions\.db|claude-archive)'; then
    # Search-style query -> hard deny (sentinel doesn't help here)
    if printf '%s' "$command" | grep -qiE '(LIKE[[:space:]]|MATCH[[:space:]]|msg_fts|GLOB[[:space:]])'; then
        deny_with_reason "Raw sqlite3 SEARCH against sessions.db is forbidden — use csearch (FTS5) or vsearch (semantic) instead. Reasons: (a) csearch already returns ts + project + role + 258 chars per hit, covers credential / history / context lookups, (b) sqlite3 LIKE is slower than FTS5 MATCH, (c) forcing csearch keeps archive-access discipline post-compact. csearch syntax: phrase '\"...\"', boolean AND/OR/NOT, --limit N (default 20). For deeper drill-down, extend csearch tooling, not raw SQL."
    fi
    # Metadata / schema queries -> allow only if sentinel valid
    if sentinel_valid; then
        exit 0
    fi
    deny_with_reason "Even metadata sqlite3 against sessions.db requires preflight — run vsearch or csearch first to confirm intent and unlock sentinel. (Sentinel may have expired after 30 min — post-compact gap; re-running vsearch refreshes it.)"
fi

# 3. Bash grep / cat / head / tail / less / more / sed / awk on memory file
if [ -n "$command" ] && printf '%s' "$command" | grep -qE "(^|[^A-Za-z0-9_])(grep|cat|head|tail|less|more|sed|awk)([^A-Za-z0-9_]|$).*${mem_dir_re}"; then
    if sentinel_valid; then
        exit 0
    fi
    deny_with_reason "Memory file is a stale INDEX, not source of truth. For roster / device / credential / history queries, run vsearch first (default) or csearch (known phrase / IP / identifier). Memory grep is allowed only after vsearch/csearch unlocks the sentinel — or for 'recent context I just discussed this session' lookups. See ~/.claude/CLAUDE.md → 'Memory file 不是 archive 替代' section."
fi

# 4. Read tool on memory file
if [ "$tool_name" = "Read" ] && [ -n "$file_path" ] && printf '%s' "$file_path" | grep -qE "$mem_dir_re"; then
    if sentinel_valid; then
        exit 0
    fi
    # Allow MEMORY.md (the index file itself) — it is loaded by system anyway
    if printf '%s' "$file_path" | grep -qE '/MEMORY\.md$'; then
        exit 0
    fi
    deny_with_reason "Memory file is a stale INDEX, not source of truth. For roster / device / credential / history queries, run vsearch first (default) or csearch (known phrase / IP / identifier). Read on memory/*.md is allowed only after vsearch/csearch unlocks the sentinel — or for 'recent context I just discussed this session' lookups. See ~/.claude/CLAUDE.md → 'Memory file 不是 archive 替代' section."
fi

# 5. SSH command containing investigative log-grep pattern
#    (e.g. "ssh ... grep ... /var/log/...", "ssh nas tail -f log")
#    The intent is "look up something in remote logs" — archive may already have it.
if [ -n "$command" ] && \
   printf '%s' "$command" | grep -qE 'ssh[[:space:]]' && \
   printf '%s' "$command" | grep -qE '(grep|cat|tail|head|less|sed|awk|find)[[:space:]]' && \
   printf '%s' "$command" | grep -qE '/var/log/|\.log[[:space:]"'\''|]|\.log\.gz'; then
    if sentinel_valid; then
        exit 0
    fi
    deny_with_reason "About to SSH and grep/cat/tail a log file. Investigative work like this often duplicates a prior session — vsearch first to see if the answer is already in the archive. If it's genuinely a new investigation, vsearch returns 0 results and still sets the sentinel, which then unlocks subsequent SSH log queries."
fi

# 6. Bash local grep/cat/tail on /var/log/* or *.log
if [ -n "$command" ] && \
   printf '%s' "$command" | grep -qE '(^|[^A-Za-z0-9_])(grep|cat|tail|head|less|sed|awk)([^A-Za-z0-9_]|$)[^|]*(/var/log/|\.log[[:space:]"'\''|]|\.log\.gz)'; then
    if sentinel_valid; then
        exit 0
    fi
    deny_with_reason "About to grep/cat a log file locally. Same logic as remote SSH log queries — vsearch first to see if a prior session already extracted this. If genuinely new, vsearch returns 0 and the sentinel still unlocks."
fi

# 7. git log --grep / -S (investigative git history search)
if [ -n "$command" ] && \
   printf '%s' "$command" | grep -qE 'git[[:space:]]+log[[:space:]]' && \
   printf '%s' "$command" | grep -qE '(--grep[=[:space:]]|--all-match|-S[[:space:]"'\''])'; then
    if sentinel_valid; then
        exit 0
    fi
    deny_with_reason "git log --grep / -S is investigative — same logic as log file grep. vsearch first; if genuinely new investigation the sentinel still unlocks after."
fi

exit 0
