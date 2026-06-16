#!/usr/bin/env bash
# publish-graph.sh — deploy a rendered graph HTML (+ optional self-hosted lib/) to a
# static web host over SSH. Generic + parameterised — NO site-specific paths baked in.
#
# Usage:
#   publish-graph.sh <local.html> <ssh-host> <remote-dir> [--with-lib <local-lib-dir>]
#
# Examples:
#   # behind an existing nginx/Authelia dashboard web-root:
#   publish-graph.sh out.html mybox /opt/dashboard
#   # air-gapped, ship the self-hosted libs too:
#   publish-graph.sh out.html mybox /opt/dashboard --with-lib ./examples/lib
#
# Auth: relies on your SSH config / agent / sshpass env — this script does not handle
# credentials. Keep secrets out of arguments.
set -euo pipefail
[ $# -ge 3 ] || { echo "usage: publish-graph.sh <local.html> <ssh-host> <remote-dir> [--with-lib <dir>]" >&2; exit 2; }
HTML="$1"; HOST="$2"; RDIR="$3"; shift 3
[ -f "$HTML" ] || { echo "not found: $HTML" >&2; exit 1; }

ssh "$HOST" "mkdir -p '$RDIR'"
scp "$HTML" "$HOST:$RDIR/"
echo "published $(basename "$HTML") → $HOST:$RDIR/"

if [ "${1:-}" = "--with-lib" ] && [ -n "${2:-}" ]; then
  LIB="$2"
  ssh "$HOST" "mkdir -p '$RDIR/lib'"
  scp "$LIB"/*.min.js "$HOST:$RDIR/lib/"
  echo "published lib/*.min.js → $HOST:$RDIR/lib/  (self-host mode)"
fi
echo "reminder: generation runs where the archive is reachable (crs/claude); this only ships the static output."
