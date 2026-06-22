#!/bin/bash
# Polite background orient-layer backfill: distill a small batch of the
# newest-still-undistilled msg rows each run. Driven by launchd
# com.jrjohn.crs-distill (StartInterval). Chunked persistence in crs means a
# kill mid-batch only loses the in-flight chunk (≤10 rows).
#
# Politeness: small batch + long interval → GPU duty cycle ~25%, so interactive
# osearch/vsearch query-embeds mostly hit idle windows. Bump BATCH / shorten the
# plist StartInterval to go faster; unload the job to pause entirely.

set -u
[ -f "$HOME/.config/crs/env.sh" ] && source "$HOME/.config/crs/env.sh"
CRS="$HOME/claude-archive/crs/target/release/crs"
BATCH="${CRS_DISTILL_BATCH:-15}"

# Atomic mkdir lock — launchd fires on schedule regardless of a prior run still
# going; this skips overlap. (macOS has no flock.)
LOCK=/tmp/crs-distill.lock
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "$(date '+%F %T') already running, skip"
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

# Skip if Ollama is down (don't spin failing).
curl -s --max-time 4 http://localhost:11434/api/tags >/dev/null 2>&1 || { echo "$(date '+%F %T') ollama down, skip"; exit 0; }

echo "=== $(date '+%F %T') distill-backfill batch=$BATCH ==="
# Global, newest-first (crs orders by id DESC), workers=1 (single GPU, no contention).
exec "$CRS" distill-missing --limit "$BATCH" --workers 1
