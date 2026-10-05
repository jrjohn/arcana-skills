#!/bin/bash
# CONTINUOUS background orient-layer backfill: loop distilling small batches of
# the newest-still-undistilled msg rows, with a short gap between batches so
# interactive osearch/vsearch GPU query-embeds can slip in. Driven by launchd
# com.jrjohn.crs-distill with KeepAlive=true (relaunches on exit / crash / reboot).
#
# Chunked persistence in crs means a kill mid-batch loses only the in-flight
# chunk (≤10 rows); re-run resumes. Local-GPU only (bluesea/cloud only query).
#
# Tunables (env): CRS_DISTILL_BATCH          rows per batch            (default 20)
#                 CRS_DISTILL_GAP            seconds between batches   (default 5)
#                 CRS_DISTILL_WORKERS        parallel generations      (default 2)
#                 CRS_DISTILL_WATCHDOG       max seconds per batch     (default 1800)
#                 CRS_DISTILL_PROJECT_PREFIX only distill these projects (default: all)
# Pause entirely: launchctl unload ~/Library/LaunchAgents/com.jrjohn.crs-distill.plist
#
# ── 2026-09-24: why the watchdog, the timestamps and the "0 pending" fix ──────
# Measured over seven days the worker was idle ~60% of the time: active hours
# produced 200-260 rows/h (keeping ahead of ingest), but whole stretches produced
# nothing — 02:48→10:24 on 09-24 while bluesea was hung, and nearly all of the
# 09-19/20 weekend. distill-missing uses the synchronous postgres client, which on
# macOS has no TCP_USER_TIMEOUT and an unbounded read: a stalled server connection
# does not fail, it waits — for hours. The watchdog does not need to know WHAT
# stalled (PG, Ollama, the network); anything slower than the limit is killed and
# the next batch starts, so an outage costs minutes instead of a night.
#
# The log printed no timestamps on batch lines, so reconstructing when the worker
# stopped meant cross-referencing insert times in the database. Every batch line
# now starts with the wall-clock time and the exit code.
#
# The completion test was `grep -q "0 pending"`, which also matches "182100
# pending", "40 pending" — any count ending in 0. It declared the backlog done
# and exited roughly once in ten batches with 180k rows still to go. It now
# matches only the exact line crs prints for a genuinely empty queue.

set -u
[ -f "$HOME/.config/crs/env.sh" ] && source "$HOME/.config/crs/env.sh"
CRS="$HOME/claude-archive/crs/target/release/crs"
BATCH="${CRS_DISTILL_BATCH:-20}"
GAP="${CRS_DISTILL_GAP:-5}"
WATCHDOG="${CRS_DISTILL_WATCHDOG:-1800}"
PREFIX_ARG=()
[ -n "${CRS_DISTILL_PROJECT_PREFIX:-}" ] && PREFIX_ARG=("--project-prefix=${CRS_DISTILL_PROJECT_PREFIX}")

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

# Milestone state: baseline pending (set once) + highest 10k milestone logged.
# cumulative-distilled-this-campaign = baseline - current_pending, parsed from
# distill-missing's own "N pending" line (no extra DB query).
STATE="$HOME/claude-archive/distill-backfill.state"

echo "=== $(date '+%F %T') distill-backfill CONTINUOUS (batch=$BATCH gap=${GAP}s watchdog=${WATCHDOG}s prefix=${CRS_DISTILL_PROJECT_PREFIX:-all}) ==="
while true; do
  curl -s --max-time 4 http://localhost:11434/api/tags >/dev/null 2>&1 \
    || { echo "$(date '+%F %T') ollama down, exit (launchd KeepAlive will relaunch)"; exit 0; }

  # macOS ships no `timeout`; perl's alarm survives exec, so SIGALRM lands on crs
  # itself and terminates it (exit 142 = 128 + SIGALRM).
  out=$(perl -e 'alarm shift; exec @ARGV or die "exec: $!"' "$WATCHDOG" \
        "$CRS" distill-missing --limit "$BATCH" --workers "${CRS_DISTILL_WORKERS:-2}" \
        ${PREFIX_ARG[@]+"${PREFIX_ARG[@]}"} 2>&1)
  rc=$?

  pending=$(printf '%s\n' "$out" | grep -oE '^distill-missing: [0-9]+ pending' | grep -oE '[0-9]+' | head -1)
  errs=$(printf '%s\n' "$out" | grep -c 'err=')
  summary=$(printf '%s\n' "$out" | grep -E '^done\.' | tail -1)
  if [ "$rc" -eq 142 ]; then
    echo "$(date '+%F %T') ⏱ WATCHDOG killed batch after ${WATCHDOG}s (pending=${pending:-?}) — something stalled; next batch starts fresh"
  else
    echo "$(date '+%F %T') rc=$rc pending=${pending:-?} errs=$errs | ${summary:-(no done line)}"
  fi
  # Surface errors instead of filtering them out: an insert that fails every row
  # used to leave only "done. distilled 40 rows" in this log.
  [ "$errs" -gt 0 ] && printf '%s\n' "$out" | grep 'err=' | head -3 | sed 's/^/    /'

  # --- milestone markers (every 10k 📍, every 50k 🎯) ---
  if [ -n "${pending:-}" ]; then
    if [ ! -f "$STATE" ]; then printf 'baseline=%s\nmilestone=0\n' "$pending" > "$STATE"; fi
    baseline=$(grep '^baseline=' "$STATE" | cut -d= -f2)
    last_ms=$(grep '^milestone=' "$STATE" | cut -d= -f2)
    cumulative=$(( baseline - pending ))
    new_ms=$(( cumulative / 10000 * 10000 ))
    if [ "$new_ms" -gt "${last_ms:-0}" ]; then
      marker="📍"; [ $(( new_ms % 50000 )) -eq 0 ] && marker="🎯🎯🎯"
      echo "$(date '+%F %T') $marker MILESTONE: ~$cumulative distilled this campaign ($pending pending left, baseline $baseline)"
      printf 'baseline=%s\nmilestone=%s\n' "$baseline" "$new_ms" > "$STATE"
    fi
  fi

  # Genuinely empty queue: idle instead of exiting. Exiting hands control to
  # launchd KeepAlive, which relaunches within seconds, finds the queue still
  # empty and exits again — a restart storm for as long as there is no backlog.
  if [ "${pending:-x}" = "0" ]; then
    echo "$(date '+%F %T') backlog empty — idle 10 min before checking again"
    sleep 600
    continue
  fi
  sleep "$GAP"
done
