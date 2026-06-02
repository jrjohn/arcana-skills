#!/usr/bin/env bash
# Demo aid: start a fresh ci-flow instance every INTERVAL seconds so the
# dashboard always shows instances in flight (the task-worker advances them).
# Not part of the platform — stop with Ctrl-C.
set -euo pipefail
ENGINE="${ENGINE_URL:-http://localhost:8081}/ci-flow"
INTERVAL="${INTERVAL:-12}"
prs=(57 61 44 70 88 92 103 7 19 145)
i=0
echo "demo-seed: one ci-flow every ${INTERVAL}s -> $ENGINE (Ctrl-C to stop)"
while true; do
  pr=${prs[$((i % ${#prs[@]}))]}
  curl -s -X POST "$ENGINE" -H 'Content-Type: application/json' \
    -d "{\"subject\":\"PR #${pr} CI failure\"}" -o /dev/null \
    -w "seeded PR #${pr} -> %{http_code}\n"
  i=$((i + 1))
  sleep "$INTERVAL"
done
