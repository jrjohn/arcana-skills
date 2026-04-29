#!/bin/bash
# gen-recent-context.sh — Auto-generate per-project recent context for Memory.
#
# Triggered by SessionStart hook (or manual run). Pulls:
#   1. Open pending items from <project>/memory/project_pending.md
#   2. Last 8 distinct user prompts in last 48h (from session.db)
#   3. Last 5 substantive (≥200-char) assistant responses in last 48h
#
# Writes ~/.claude/projects/<slug>/memory/auto_recent.md
#
# Source for the project comes from (priority order):
#   1. $CLAUDE_PROJECT_SLUG env var      ← used by build.py 15-min cron loop
#   2. JSON on stdin: {"cwd": "..."}     ← SessionStart hook input
#   3. $CLAUDE_PROJECT_DIR env var
#   4. $PWD                              ← fallback when run interactively
#
# Skips silently if the resolved project has no memory dir
# (not a known project, OR not yet seen by Claude Code).

set -e

DB=$HOME/claude-archive/sessions.db
[ -f "$DB" ] || { echo "(no session.db, skipping)"; exit 0; }

# 1. Resolve slug (priority: env > stdin JSON > PWD)
SLUG="${CLAUDE_PROJECT_SLUG:-}"
if [ -z "$SLUG" ]; then
    PROJECT_DIR=""
    if [ ! -t 0 ]; then
        INPUT=$(cat)
        if [ -n "$INPUT" ]; then
            PROJECT_DIR=$(printf '%s' "$INPUT" | python3 -c 'import json,sys; d=json.loads(sys.stdin.read() or "{}"); print(d.get("cwd",""))' 2>/dev/null)
        fi
    fi
    [ -z "$PROJECT_DIR" ] && PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
    SLUG=$(printf '%s' "$PROJECT_DIR" | sed 's|/|-|g')
fi
MEM_DIR="$HOME/.claude/projects/$SLUG/memory"
PENDING="$MEM_DIR/project_pending.md"
OUT="$MEM_DIR/auto_recent.md"

# 3. Skip if not a known project (no memory dir or no pending file)
if [ ! -d "$MEM_DIR" ]; then
    exit 0
fi

NOW=$(date '+%Y-%m-%d %H:%M')
SINCE_TS=$(date -v-48H '+%Y-%m-%dT%H:%M:%S' 2>/dev/null || date -d '48 hours ago' '+%Y-%m-%dT%H:%M:%S')

# 4. Generate
{
    cat <<MD
---
name: 自動最近 context
description: 每次 session 開始由 SessionStart hook 自動產生：當前 pending + 最近 48h 主要對話事件，方便 Claude 第一秒就有 context
type: project
auto-generated: true
last-update: $NOW
---

# 🔄 自動最近 context (生成於 $NOW)

> 由 \`gen-recent-context.sh\` 自動更新，project=\`$SLUG\`。要改邏輯改那個檔。

MD

    if [ -f "$PENDING" ]; then
        echo "## 📋 待處理事項（從 project_pending.md 截取）"
        echo
        awk '
          /^## 待處理/ { flag=1; print; next }
          /^## / && flag { exit }
          flag { print }
        ' "$PENDING" | head -60
        echo
    fi

    echo "## 🗣️ 最近 48h 主要使用者意圖（dedupe，從 session.db）"
    echo
    sqlite3 "$DB" "
SELECT substr(ts,1,16) AS t, substr(content,1,160) AS msg
FROM msg
WHERE project='$SLUG'
  AND ts >= '$SINCE_TS'
  AND role='user'
  AND content NOT LIKE '[TOOL_RESULT]%'
  AND content NOT LIKE '<%'
  AND length(content) BETWEEN 4 AND 300
ORDER BY ts DESC
LIMIT 40
" 2>/dev/null | awk -F'|' '
        {
            key = substr($2, 1, 30)
            if (seen[key]++) next
            if (++count > 8) exit
            print "- **" $1 "** — " $2
        }
    '
    echo

    echo "## 🔧 最近 48h 工作主題（assistant ≥200 字回應）"
    echo
    sqlite3 "$DB" "
SELECT substr(ts,1,16) AS t, substr(replace(content, X'0A', ' '), 1, 180) AS msg
FROM msg
WHERE project='$SLUG'
  AND ts >= '$SINCE_TS'
  AND role='assistant'
  AND content NOT LIKE '[TOOL_USE%'
  AND content NOT LIKE '[THINKING%'
  AND length(content) >= 200
ORDER BY ts DESC
LIMIT 15
" 2>/dev/null | awk -F'|' '
        {
            if (++count > 5) exit
            print "- **" $1 "** — " $2 " ..."
        }
    '
    echo
    echo "---"
    echo "*Auto-regenerated on every \`claude\` start. To force refresh now: \`~/claude-archive/gen-recent-context.sh\`*"
} > "$OUT"

echo "wrote $OUT ($(wc -l < $OUT) lines, project=$SLUG)"
