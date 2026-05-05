#!/usr/bin/env bash
# PreToolUse hook (Bash + Read) — enforce vsearch / csearch preflight before:
#   (a) raw sqlite3 against ~/claude-archive/sessions.db, or
#   (b) grep / cat / head / tail / less / more / sed / awk on a memory file
#       in ~/.claude/projects/*/memory/*.md, or
#   (c) Read tool reading the same memory files.
#
# Why memory enforcement: memory files are stale, hand-curated indexes
# (incomplete by design). For roster / device / credential / history
# queries, the canonical source is the archive DB. csearch/vsearch return
# the actual past conversation transcript verbatim; memory grep returns
# only what someone manually wrote down. Forcing vsearch/csearch first
# prevents the "I'll just grep memory and miss half the data" antipattern.
#
# Behavior:
#   - vsearch / csearch invocation -> set sentinel, allow.
#   - sqlite3 against archive DB    -> allow only if sentinel exists.
#   - grep/cat/.../Read on memory   -> allow only if sentinel exists.
#   - Read on MEMORY.md (the index) -> always allow (auto-loaded by system).
#   - Otherwise: allow silently.
#
# Sentinel: /tmp/claude-archive-preflight-<session_id>
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

# 1. vsearch / csearch invocation -> mark preflight done
if [ -n "$command" ] && printf '%s' "$command" | grep -qE '(^|[^A-Za-z0-9_])(vsearch|csearch)([^A-Za-z0-9_]|$)'; then
    : > "$sentinel"
    exit 0
fi

# 2. raw sqlite3 against the archive DB
if [ -n "$command" ] && printf '%s' "$command" | grep -qE 'sqlite3([[:space:]]|$).*(sessions\.db|claude-archive)'; then
    if [ -e "$sentinel" ]; then
        exit 0
    fi
    deny_with_reason "Preflight rule (~/.claude/CLAUDE.md): run vsearch first (csearch for exact IP/hostname/filename) before raw sqlite3 against ~/claude-archive/sessions.db. Invoke vsearch or csearch in this session — it sets a sentinel and unblocks subsequent SQL queries."
fi

# 3. Bash grep / cat / head / tail / less / more / sed / awk on memory file
if [ -n "$command" ] && printf '%s' "$command" | grep -qE "(^|[^A-Za-z0-9_])(grep|cat|head|tail|less|more|sed|awk)([^A-Za-z0-9_]|$).*${mem_dir_re}"; then
    if [ -e "$sentinel" ]; then
        exit 0
    fi
    deny_with_reason "Memory file is a stale INDEX, not source of truth. For roster / device / credential / history queries, run vsearch first (default) or csearch (known phrase / IP / identifier). Memory grep is allowed only after vsearch/csearch unlocks the sentinel — or for 'recent context I just discussed this session' lookups. See ~/.claude/CLAUDE.md → 'Memory file 不是 archive 替代' section."
fi

# 4. Read tool on memory file
if [ "$tool_name" = "Read" ] && [ -n "$file_path" ] && printf '%s' "$file_path" | grep -qE "$mem_dir_re"; then
    if [ -e "$sentinel" ]; then
        exit 0
    fi
    # Allow MEMORY.md (the index file itself) — it is loaded by system anyway
    if printf '%s' "$file_path" | grep -qE '/MEMORY\.md$'; then
        exit 0
    fi
    deny_with_reason "Memory file is a stale INDEX, not source of truth. For roster / device / credential / history queries, run vsearch first (default) or csearch (known phrase / IP / identifier). Read on memory/*.md is allowed only after vsearch/csearch unlocks the sentinel — or for 'recent context I just discussed this session' lookups. See ~/.claude/CLAUDE.md → 'Memory file 不是 archive 替代' section."
fi

exit 0
