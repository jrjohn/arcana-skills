#!/bin/bash
# gen-recent-context.sh — Auto-generate per-project recent context for Memory.
#
# Triggered by SessionStart hook + every-15-min crs build cron. Writes a
# single section: vsearch ranking of last-48h msgs against the project's
# pending list. Pending excerpt itself is NOT duplicated — Claude reads
# project_pending.md directly via MEMORY.md index when it needs that.
#
# Skip guard:
#   regen only if (pending mtime > auto_recent mtime)
#                 OR (newest msg ts > auto_recent mtime)
#                 OR (FORCE_REGEN=1)
#   Otherwise exit early without touching Ollama / KNN / disk write.
#
# Writes ~/.claude/projects/<slug>/memory/auto_recent.md
#
# Source for the project comes from (priority order):
#   1. $CLAUDE_PROJECT_SLUG env var      ← used by crs build 15-min cron loop
#   2. JSON on stdin: {"cwd": "..."}     ← SessionStart hook input
#   3. $CLAUDE_PROJECT_DIR env var
#   4. $PWD                              ← fallback when run interactively
#
# Skips silently if the resolved project has no memory dir
# (not a known project, OR not yet seen by Claude Code).

set -e

LOG=$HOME/claude-archive/gen-recent-context.log
log() { printf '%s [%s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S')" "$1" "$2" >> "$LOG"; }
trap 'log ERROR "uncaught failure at line $LINENO (slug=${SLUG:-unresolved})"' ERR

DB=$HOME/claude-archive/sessions.db
[ -f "$DB" ] || { log SKIP "no session.db"; echo "(no session.db, skipping)"; exit 0; }

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
    log SKIP "unknown project slug=$SLUG (no memory dir)"
    exit 0
fi

# 3.5. Skip guard: nothing-changed → exit early, save Ollama/CPU.
#   - FORCE_REGEN=1 bypasses (use for dev / manual debugging)
#   - First run (no $OUT yet) always regens
if [ "${FORCE_REGEN:-0}" != "1" ] && [ -f "$OUT" ]; then
    LAST_GEN_TS=$(stat -f %m "$OUT" 2>/dev/null || stat -c %Y "$OUT" 2>/dev/null || echo 0)
    PENDING_TS=0
    [ -f "$PENDING" ] && PENDING_TS=$(stat -f %m "$PENDING" 2>/dev/null || stat -c %Y "$PENDING" 2>/dev/null || echo 0)
    LATEST_MSG_TS=$(sqlite3 -cmd ".headers off" -cmd ".mode list" "$DB" \
        "SELECT IFNULL(strftime('%s', MAX(ts)), 0) FROM msg WHERE project='$SLUG'" 2>/dev/null || echo 0)
    LATEST_MSG_TS=${LATEST_MSG_TS:-0}

    if [ "$PENDING_TS" -le "$LAST_GEN_TS" ] && [ "$LATEST_MSG_TS" -le "$LAST_GEN_TS" ]; then
        log SKIP "no changes (slug=$SLUG, last_gen=$LAST_GEN_TS, pending=$PENDING_TS, latest_msg=$LATEST_MSG_TS)"
        exit 0
    fi
fi

NOW=$(date '+%Y-%m-%d %H:%M')
SINCE_TS=$(date -v-48H '+%Y-%m-%dT%H:%M:%S' 2>/dev/null || date -d '48 hours ago' '+%Y-%m-%dT%H:%M:%S')

# 4. Generate
{
    cat <<MD
---
name: 自動最近 context
description: 最近 48h 跟 pending 語意相關的對話 snippets（vsearch ranking）。pending 條目本身請讀 project_pending.md，不要兩邊都讀
type: project
auto-generated: true
last-update: $NOW
---

# 🔄 最近 48h 跟 pending 語意相關的訊息

> vsearch on pending → KNN over msg_vec (cosine, max-distance 0.65)。
> project=\`$SLUG\`。要改邏輯動 \`gen-recent-context.sh\`。

MD

    CRS_BIN="$HOME/claude-archive/crs/target/release/crs"

    if [ ! -x "$CRS_BIN" ]; then
        echo "_(vsearch-since 不可用：crs binary 缺)_"
    elif [ ! -f "$PENDING" ]; then
        echo "_(無 pending 檔可當 query seed)_"
    else
        QUERY=$(awk '
              /^## 待處理/ { flag=1; next }
              /^## / && flag { exit }
              flag { print }
            ' "$PENDING" | tr '\n' ' ' | sed 's/[*#`]//g' | cut -c1-1500)

        if [ -z "$QUERY" ]; then
            echo "_(pending list 空，無 query seed)_"
        else
            # --flag=value form: SLUG starts with '-' which clap could mis-read
            # as another flag in space-separated form.
            "$CRS_BIN" vsearch-since \
                --query="$QUERY" \
                --project="$SLUG" \
                --hours=48 \
                --limit=6 \
                --max-distance=0.65 \
                --max-snippet=140 2>>"$LOG" \
                || echo "_(vsearch-since 失敗 — 看 $LOG)_"
        fi
    fi
    echo
    echo "---"
    echo "*Regen on SessionStart + 15-min cron, with skip guard. Force: \`FORCE_REGEN=1 ~/claude-archive/gen-recent-context.sh\`*"
} > "$OUT"

LINES=$(wc -l < "$OUT" | tr -d ' ')
log OK "wrote $OUT ($LINES lines, project=$SLUG)"
echo "wrote $OUT ($LINES lines, project=$SLUG)"
