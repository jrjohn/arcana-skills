#!/bin/bash
# CONTINUOUS background orient-layer backfill: loop distilling small batches of
# the newest-still-undistilled msg rows, with a short gap between batches so
# interactive osearch/vsearch GPU query-embeds can slip in. Driven by launchd
# com.jrjohn.crs-distill with KeepAlive=true (relaunches on exit / crash / reboot).
#
# Chunked persistence in crs means a kill mid-batch loses only the in-flight
# chunk (≤10 rows); re-run resumes. Local-GPU only (bluesea/cloud only query).
#
# Tunables (env): CRS_DISTILL_BATCH (rows per batch, default 20),
#                 CRS_DISTILL_GAP   (seconds between batches, default 5).
# Pause entirely: launchctl unload ~/Library/LaunchAgents/com.jrjohn.crs-distill.plist

set -u
[ -f "$HOME/.config/crs/env.sh" ] && source "$HOME/.config/crs/env.sh"
CRS="$HOME/claude-archive/crs/target/release/crs"
BATCH="${CRS_DISTILL_BATCH:-20}"
GAP="${CRS_DISTILL_GAP:-5}"

# Single-instance guard, stale-safe (clears the lock if the holder PID is gone).
# KeepAlive already serialises launchd runs; this also blocks stray manual runs.
LOCK=/tmp/crs-distill.lock
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -f "$LOCK/pid" ] && kill -0 "$(cat "$LOCK/pid" 2>/dev/null)" 2>/dev/null; then
    echo "$(date '+%F %T') already running (pid $(cat "$LOCK/pid")), skip"; exit 0
  fi
  echo "$(date '+%F %T') clearing stale lock"; rm -rf "$LOCK"; mkdir "$LOCK" || exit 0
fi
echo $$ > "$LOCK/pid"
trap 'rm -rf "$LOCK" 2>/dev/null' EXIT

echo "=== $(date '+%F %T') distill-backfill CONTINUOUS (batch=$BATCH gap=${GAP}s) ==="
while true; do
  curl -s --max-time 4 http://localhost:11434/api/tags >/dev/null 2>&1 \
    || { echo "$(date '+%F %T') ollama down, exit (launchd KeepAlive will relaunch)"; exit 0; }
  out=$("$CRS" distill-missing --limit "$BATCH" --workers 1 2>&1)
  echo "$out" | grep -E "pending|chunk persisted|done\." | tail -2
  if echo "$out" | grep -q "0 pending"; then
    echo "$(date '+%F %T') backfill COMPLETE — nothing left to distill, exit"; exit 0
  fi
  sleep "$GAP"
done
