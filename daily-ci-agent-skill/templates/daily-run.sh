#!/usr/bin/env bash
# Daily CI agent driver: invoke claude with the daily prompt.
set -euo pipefail

LOG_PREFIX=$(date '+%Y-%m-%d %H:%M:%S')
REPORT_DATE=$(date +%F)
REPORT_DIR=/data/ci-reports
REPORT_PATH="${REPORT_DIR}/${REPORT_DATE}.md"
PROMPT_FILE=/opt/prompt/daily.md
CLAUDE_BIN=$(command -v claude || echo /usr/local/bin/claude)

mkdir -p "$REPORT_DIR"

echo "=== ${LOG_PREFIX} daily-run start ==="

if [ ! -x "$CLAUDE_BIN" ]; then
  echo "ERROR: claude CLI not found at $CLAUDE_BIN"; exit 1
fi
if [ ! -r "$PROMPT_FILE" ]; then
  echo "ERROR: prompt file missing: $PROMPT_FILE"; exit 1
fi
if [ ! -f /root/.claude/.credentials.json ]; then
  echo "ERROR: Claude not authenticated. Run: docker exec -it daily-ci-agent claude /login"
  echo "# Daily CI report — ${REPORT_DATE}" > "$REPORT_PATH"
  echo "" >> "$REPORT_PATH"
  echo "**ERROR**: Claude CLI not authenticated in container. Re-run OAuth setup." >> "$REPORT_PATH"
  exit 1
fi

export REPORT_PATH REPORT_DATE

PROMPT_CONTENT=$(cat "$PROMPT_FILE")
# Drop privileges to claude-agent (claude CLI refuses --dangerously-skip-permissions as root)
/usr/sbin/runuser -u claude-agent -- env HOME=/root REPORT_PATH="$REPORT_PATH" REPORT_DATE="$REPORT_DATE" \
  "$CLAUDE_BIN" --print --dangerously-skip-permissions "$PROMPT_CONTENT"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') daily-run done (report: $REPORT_PATH) ==="
