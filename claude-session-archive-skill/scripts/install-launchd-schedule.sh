#!/bin/bash
# Install / refresh the macOS 15-minute ingest schedule for claude-session-archive.
# Called by install.sh; safe to run on its own and safe to run again.
#
#   install-launchd-schedule.sh <SKILL_DIR> <WITH_PG: 0|1>
#
# What it guarantees — each rule is here because breaking it broke a real install:
#
#   • ~/.config/crs/env.sh is NEVER overwritten. It is the only place credentials
#     live. It is created only when missing.
#   • An existing plist with REAL inline credentials (the old template's style)
#     has them MOVED into env.sh before the plist is replaced — never dropped.
#   • A plist that already runs the launcher and carries no credentials is left
#     alone and NOT reloaded, so a re-run does not kill a build in progress.
#   • Anything replaced is backed up to <file>.bak-<timestamp> first.
#   • bootstrap is retried: right after bootout, launchd can still be tearing the
#     old job down and returns "Bootstrap failed: 5: Input/output error" — seen on
#     2026-09-24 deploying the distill worker; the same call succeeded seconds later.
#
# LAUNCHCTL and PLISTBUDDY can be overridden (tests use a fake launchctl so a run
# against a scratch HOME never touches the real launchd domain).
set -euo pipefail

SKILL_DIR="${1:?usage: install-launchd-schedule.sh <SKILL_DIR> <WITH_PG>}"
WITH_PG="${2:-0}"
LAUNCHCTL="${LAUNCHCTL:-launchctl}"
PB="${PLISTBUDDY:-/usr/libexec/PlistBuddy}"

USER_SHORT="$(id -un)"
LABEL="com.${USER_SHORT}.claude-archive"
ARCHIVE_DIR="$HOME/claude-archive"
LAUNCHER="$ARCHIVE_DIR/bin/crs-build-launcher"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
ENV_SH="$HOME/.config/crs/env.sh"
TS="$(date +%Y%m%d-%H%M%S)"

PLACEHOLDER_HOST="arcana.example.com"
PLACEHOLDER_PW="REPLACE_WITH_YOUR_PG_PASSWORD"

# Only trust PlistBuddy's stdout when it exits 0. On an unreadable file it prints
# "Error Reading File: …" to STDOUT with rc=1 — the first version of this helper
# took that text as the password and wrote it into env.sh as a "migrated
# credential" (caught by the test suite, not in the field).
pb_get() {
  local v
  if v="$("$PB" -c "Print :$1" "$2" 2>/dev/null)"; then printf '%s' "$v"; fi
}

# An existing plist we cannot parse is a stop sign, not something to overwrite:
# it may hold the only copy of real credentials, and we could not read them out.
if [ -f "$PLIST" ] && ! plutil -lint "$PLIST" >/dev/null 2>&1; then
  echo "    !! $PLIST exists but is not a valid plist:" >&2
  # `|| true`: plutil -lint fails on this file BY DESIGN — that is what we are
  # showing. Without it, set -e + pipefail killed the script on this line and the
  # explanation below never printed; the refusal happened, but by accident.
  plutil -lint "$PLIST" 2>&1 | sed 's/^/       /' >&2 || true
  echo "       Refusing to overwrite it — it may hold your only copy of the PG credentials." >&2
  echo "       Fix or move it aside, put the credentials in $ENV_SH, then re-run." >&2
  exit 1
fi

# ── 1. launcher ──────────────────────────────────────────────────────────────
mkdir -p "$ARCHIVE_DIR/bin" "$HOME/Library/LaunchAgents"
if [ -f "$LAUNCHER" ] && ! cmp -s "$SKILL_DIR/scripts/crs-build-launcher" "$LAUNCHER"; then
  cp "$LAUNCHER" "$LAUNCHER.bak-$TS"
  echo "    launcher differs from the skill's — previous kept as $(basename "$LAUNCHER").bak-$TS"
fi
install -m 755 "$SKILL_DIR/scripts/crs-build-launcher" "$LAUNCHER"
echo "    launcher: $LAUNCHER"

# ── 2. env.sh ────────────────────────────────────────────────────────────────
# Migration runs whatever WITH_PG says. The 2026-07-23 breakage came from a run
# WITHOUT --with-pg on a PG install; gating the rescue on the flag would lose
# real credentials in exactly that case.
old_host=""; old_pw=""
if [ -f "$PLIST" ]; then
  old_host="$(pb_get EnvironmentVariables:CRS_PG_HOST "$PLIST")"
  old_pw="$(pb_get EnvironmentVariables:CRS_PG_PASSWORD "$PLIST")"
fi
old_is_real=0
if [ -n "$old_pw" ] && [ "$old_pw" != "$PLACEHOLDER_PW" ] \
   && [ -n "$old_host" ] && [ "$old_host" != "$PLACEHOLDER_HOST" ]; then
  old_is_real=1
fi

if [ -f "$ENV_SH" ]; then
  echo "    env.sh present — left untouched: $ENV_SH"
  if [ "$old_is_real" = "1" ]; then
    echo "    (the old plist also had inline credentials; env.sh wins, the plist copy is in the .bak)"
  fi
elif [ "$old_is_real" = "1" ]; then
  mkdir -p "$(dirname "$ENV_SH")"
  ( umask 077
    {
      echo "# crs PG credentials — the ONLY place they live. Sourced by crs-build-launcher."
      echo "# Migrated $TS from the old plist's inline EnvironmentVariables."
      for k in CRS_PG_HOST CRS_PG_PORT CRS_PG_USER CRS_PG_DB CRS_PG_PASSWORD; do
        v="$(pb_get "EnvironmentVariables:$k" "$PLIST")"
        if [ -n "$v" ]; then printf 'export %s=%q\n' "$k" "$v"; fi
      done
    } > "$ENV_SH" )
  chmod 600 "$ENV_SH"
  echo "    env.sh created from the old plist's REAL credentials (moved, not dropped): $ENV_SH"
elif [ "$WITH_PG" = "1" ]; then
  mkdir -p "$(dirname "$ENV_SH")"
  ( umask 077
    cat > "$ENV_SH" <<EOF
# crs PG credentials — the ONLY place they live. Sourced by crs-build-launcher.
# Fill in, then: launchctl kickstart -k gui/\$(id -u)/$LABEL
export CRS_PG_HOST=$PLACEHOLDER_HOST
export CRS_PG_PASSWORD=$PLACEHOLDER_PW
# Defaults if unset: CRS_PG_PORT=5432 CRS_PG_USER=archive CRS_PG_DB=archive_main
EOF
  )
  chmod 600 "$ENV_SH"
  echo "    !! env.sh created with PLACEHOLDERS — edit before the next tick: $ENV_SH"
fi

# ── 3. plist ─────────────────────────────────────────────────────────────────
current=0
if [ -f "$PLIST" ] \
   && [ "$(pb_get ProgramArguments:0 "$PLIST")" = "$LAUNCHER" ] \
   && [ -z "$(pb_get EnvironmentVariables:CRS_PG_PASSWORD "$PLIST")" ] \
   && [ -z "$(pb_get EnvironmentVariables:CRS_PG_HOST "$PLIST")" ]; then
  current=1
fi

if [ "$current" = "1" ]; then
  echo "    plist already runs the launcher with no inline credentials — left as-is"
else
  if [ -f "$PLIST" ]; then
    cp "$PLIST" "$PLIST.bak-$TS"
    echo "    previous plist kept as $(basename "$PLIST").bak-$TS"
  fi
  sed -e "s|<USERNAME>|${USER_SHORT}|g" -e "s|<HOME>|${HOME}|g" \
      "$SKILL_DIR/scripts/launchd.plist.template" > "$PLIST"
  plutil -lint "$PLIST" >/dev/null
  echo "    plist written: $PLIST"
fi

# ── 4. load ──────────────────────────────────────────────────────────────────
domain="gui/$(id -u)"
loaded=0
# awk reads to EOF on purpose. `… | grep -q` exits at the first match, the
# writer upstream takes SIGPIPE, and under `set -o pipefail` the pipeline then
# reports failure — a job that IS loaded would read as not loaded.
if "$LAUNCHCTL" list 2>/dev/null | awk -v l="$LABEL" '$3 == l {f = 1} END {exit !f}'; then
  loaded=1
fi

if [ "$current" = "1" ] && [ "$loaded" = "1" ]; then
  echo "    launchd: already loaded, not reloading (a running build is left alone)"
  exit 0
fi

[ "$loaded" = "1" ] && "$LAUNCHCTL" bootout "$domain/$LABEL" 2>/dev/null || true
for attempt in 1 2 3 4 5; do
  if "$LAUNCHCTL" bootstrap "$domain" "$PLIST" 2>/dev/null; then
    echo "    launchd: loaded ($LABEL)"
    exit 0
  fi
  sleep 2
done
echo "    !! launchd bootstrap failed 5 times — load it by hand:" >&2
echo "       launchctl bootstrap $domain \"$PLIST\"" >&2
exit 1
