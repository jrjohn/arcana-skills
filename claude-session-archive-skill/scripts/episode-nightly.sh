#!/bin/bash
# Nightly EVENT extraction: turn conversations that went quiet into episodes
# (symptom → cause → fix → outcome → lesson) in msg_episode. Driven by launchd
# com.<user>.crs-episode at 02:30 (a sleeping Mac runs it on wake).
#
# Runs on the Mac, not the GPU worker: extraction is done by Claude (`claude -p`),
# because reading a whole conversation is the point and a 16K-window local model
# would have to read it in slices — the context loss this layer exists to fix.
#
# Tunables (env, or ~/.config/crs/env.sh):
#   CRS_EPISODE_MAX_SESSIONS  sessions per night                 (default 30)
#   CRS_EPISODE_DAYS          only sessions active within N days (default 90)
#   CRS_EPISODE_MAX_OUTPUT    stop after this many output tokens (default 200000)
#   CRS_EPISODE_MODEL         claude model alias                 (default sonnet)
#   CRS_EPISODE_WATCHDOG      max seconds for the whole run      (default 7200)
#   CRS_EPISODE_PROJECT_PREFIX projects to read                  (default -Users-<you>)
# Pause: launchctl bootout gui/$(id -u)/com.$(id -un).crs-episode
#
# Secrets: crs masks CRS_PG_PASSWORD, every line of ~/.config/crs/secret-literals.txt
# (one literal per line, chmod 600) and common token shapes before anything is
# written. Put the passwords you know appear in conversations in that file.

set -u
[ -f "$HOME/.config/crs/env.sh" ] && source "$HOME/.config/crs/env.sh"
CRS="$HOME/claude-archive/crs/target/release/crs"
export CRS_CLAUDE_BIN="${CRS_CLAUDE_BIN:-$HOME/.local/bin/claude}"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
WATCHDOG="${CRS_EPISODE_WATCHDOG:-7200}"
PREFIX="${CRS_EPISODE_PROJECT_PREFIX:--Users-$(id -un)}"

echo "$(date '+%F %T') start (max_sessions=${CRS_EPISODE_MAX_SESSIONS:-30}, days=${CRS_EPISODE_DAYS:-90})"
# perl alarm = a timeout macOS ships with; exit 142 means the watchdog fired.
perl -e 'alarm shift; exec @ARGV' "$WATCHDOG" \
  "$CRS" episode-missing \
    --max-sessions "${CRS_EPISODE_MAX_SESSIONS:-30}" \
    --days "${CRS_EPISODE_DAYS:-90}" \
    --project-prefix="$PREFIX"
rc=$?
[ "$rc" = 142 ] && echo "$(date '+%F %T') ⏱ WATCHDOG killed episode-missing after ${WATCHDOG}s; next night resumes per session"
echo "$(date '+%F %T') end rc=$rc"
exit "$rc"
