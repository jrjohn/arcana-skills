#!/usr/bin/env bash
# Run inside daily-ci-agent container — sets up Renovate central config + per-repo configs.
set -euo pipefail

ORG="${ORG:-YOUR-GITHUB-ORG}"  # override via env: ORG=acme bash setup-renovate.sh

echo "=== 1. Ensure ${ORG}/renovate-config repo ==="
if gh repo view "${ORG}/renovate-config" >/dev/null 2>&1; then
  echo "  exists"
else
  gh repo create "${ORG}/renovate-config" --public \
    --description "Central Renovate preset for ${ORG}/* repos"
  echo "  created"
fi

echo "=== 2. Upload default.json preset ==="
cat > /tmp/default.json <<'JSON'
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "schedule": ["before 6am on monday"],
  "timezone": "Asia/Taipei",
  "prConcurrentLimit": 5,
  "prHourlyLimit": 2,
  "labels": ["renovate"],
  "packageRules": [
    { "matchUpdateTypes": ["patch", "minor"], "automerge": true, "platformAutomerge": true },
    { "matchUpdateTypes": ["major"], "automerge": false, "labels": ["renovate", "major"] },
    { "matchPackagePatterns": ["compileSdk", "targetSdk"], "automerge": false, "labels": ["renovate", "sdk-bump"] },
    { "matchPackagePatterns": ["IPHONEOS_DEPLOYMENT_TARGET"], "automerge": false, "labels": ["renovate", "sdk-bump"] }
  ]
}
JSON

SHA=$(gh api "repos/${ORG}/renovate-config/contents/default.json" --jq .sha 2>/dev/null || true)
B64=$(base64 -w0 /tmp/default.json)
if [ -n "$SHA" ]; then
  echo "  updating existing default.json (sha=$SHA)"
  gh api -X PUT "repos/${ORG}/renovate-config/contents/default.json" \
    -f message="chore: update renovate preset" \
    -f content="$B64" -f sha="$SHA" --jq .commit.sha
else
  echo "  creating default.json"
  gh api -X PUT "repos/${ORG}/renovate-config/contents/default.json" \
    -f message="chore: add renovate preset" \
    -f content="$B64" --jq .commit.sha
fi

echo "=== 3. PUT renovate.json into each target repo ==="
REPOS=(
  # Edit this list to match your target repos. Or auto-discover:
  #   REPOS=( $(gh repo list "$ORG" --limit 100 --json name --jq '.[].name') )
  YOUR-REPO-1
  YOUR-REPO-2
)

cat > /tmp/renovate.json <<'JSON'
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["github>'"${ORG}"'/renovate-config"]
}
JSON
RB64=$(base64 -w0 /tmp/renovate.json)

for R in "${REPOS[@]}"; do
  SHA=$(gh api "repos/${ORG}/${R}/contents/renovate.json" --jq .sha 2>/dev/null || true)
  if [ -n "$SHA" ]; then
    RESULT=$(gh api -X PUT "repos/${ORG}/${R}/contents/renovate.json" \
      -f message="chore: refresh renovate config" \
      -f content="$RB64" -f sha="$SHA" --jq .commit.sha 2>&1) && STATUS="updated" || STATUS="ERR: $RESULT"
  else
    RESULT=$(gh api -X PUT "repos/${ORG}/${R}/contents/renovate.json" \
      -f message="chore: add renovate config" \
      -f content="$RB64" --jq .commit.sha 2>&1) && STATUS="created" || STATUS="ERR: $RESULT"
  fi
  printf "  %-30s %s\n" "$R" "$STATUS"
done

echo "=== done ==="
