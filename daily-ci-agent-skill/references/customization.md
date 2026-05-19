# daily-ci-agent customization

How to bend this skill for your environment beyond the default your own infra.

## Change cron schedule

`templates/crontab`:
```
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
0 9 * * * root /usr/local/bin/daily-run.sh >> /var/log/daily-run.log 2>&1
```

Format: `min hour day month weekday user command`. Examples:
- Daily 09:00: `0 9 * * *` (default)
- Twice daily 08:00 + 17:00: `0 8,17 * * *`
- Weekdays only 09:00: `0 9 * * 1-5`
- Every 4 hours: `0 */4 * * *`

After edit: `docker compose build --no-cache && docker compose up -d --force-recreate`. Cron daemon picks up the new file via entrypoint reload.

**Timezone**: `TZ=Asia/Taipei` is set in `docker-compose.ci-agent.yml` env. Change to your `TZ` value (`Asia/Tokyo`, `Europe/Berlin`, `America/Los_Angeles`, etc).

## Add / remove monitored services

Edit `templates/daily.md` → section `### 2. Service health`. Add a row to the matrix:

```markdown
| MyService | curl -sS http://myservice:8080/health | HTTP 200 AND `status: ok` |
```

Then add the same entry to the report `## Service health` skeleton:
```markdown
### MyService     — <OK|DEGRADED|DOWN> — <detail>
```

Rebuild image.

## Change monitored GitHub repos

`templates/daily.md` → section `### 1. Renovate PR review`. The agent uses `gh search prs --owner <org>` which auto-discovers. To restrict to specific repos, change to:
```
gh pr list --repo <org>/<repo> --author app/renovate --state open ...
```
and loop.

For `scripts/setup-renovate.sh` → edit the `REPOS=()` array.

## Change auto-merge rules

Edit the central preset repo's `default.json` (created by `setup-renovate.sh`). Push the change; Renovate auto-picks-up:

```json
{
  "packageRules": [
    // Auto-merge patch + minor of all deps
    { "matchUpdateTypes": ["patch", "minor"], "automerge": true, "platformAutomerge": true },
    // Never auto-merge majors
    { "matchUpdateTypes": ["major"], "automerge": false, "labels": ["renovate", "major"] },
    // Never auto-merge SDK markers
    { "matchPackagePatterns": ["compileSdk", "targetSdk", "IPHONEOS_DEPLOYMENT_TARGET"],
      "automerge": false, "labels": ["renovate", "sdk-bump"] },
    // Example: pin a specific dep to manual review
    { "matchPackageNames": ["spring-boot-starter-security"], "automerge": false },
    // Example: auto-merge ALL @types/* even major
    { "matchPackagePatterns": ["^@types/"], "automerge": true }
  ]
}
```

## Change report output path / filename

`templates/daily-run.sh`:
```bash
REPORT_DIR=/data/ci-reports
REPORT_PATH="${REPORT_DIR}/${REPORT_DATE}.md"
```

If you change the path, also update:
- nginx `alias` in `/ci-reports/` location block
- SELinux `semanage fcontext` rule
- docker-compose volume mount `/data/ci-reports:/data/ci-reports`
- `templates/daily.md` `$REPORT_PATH` references

## Change report sink (push instead of pull)

By default the report sits as a markdown file behind nginx. Alternatives:

### Push to LINE group (if you have line-notify skill)
Edit `templates/daily.md` → add at end:
```
After writing the report, also send to LINE:
  /skill line-notify <group-id> <one-line summary + URL to full report>
```

### Push to email
Append to `daily-run.sh`:
```bash
if [ -f "$REPORT_PATH" ]; then
  mail -s "Daily CI report — $REPORT_DATE" you@example.com < "$REPORT_PATH"
fi
```
Requires `apt-get install -y mailutils` + SMTP config in Dockerfile.

### Push to Slack webhook
Append to `daily-run.sh`:
```bash
SUMMARY=$(grep -A 4 "^## Summary" "$REPORT_PATH" | tail -4)
curl -sS -X POST "$SLACK_WEBHOOK_URL" -H 'Content-Type: application/json' \
  -d "$(jq -n --arg t "Daily CI — $REPORT_DATE" --arg s "$SUMMARY" '{text: ($t + "\n```" + $s + "```")}')"
```

## Use without Authelia

Drop the `auth_request` lines from the nginx `location /ci-reports/` block. **Strongly recommended to add some auth** (basic_auth, mTLS, IP allowlist) — otherwise your CI report (which lists internal service status + PR details) is public.

## Run twice (different scope)

Two patterns:
1. **Single container, two cron lines** — edit crontab to run twice with different `--prompt` files.
2. **Two containers** — duplicate `docker-compose.ci-agent.yml` (different container_name + image tag + report path).

## Switch to ANTHROPIC_API_KEY instead of OAuth

For unattended fleets where the 60-day OAuth refresh isn't tenable:
1. Anthropic Console → create API key.
2. Skip Phase B entirely.
3. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`.
4. Add to docker-compose env passthrough.
5. Use `claude --bare --print "..."` in daily-run.sh — `--bare` strips OAuth/keychain lookup and forces ANTHROPIC_API_KEY.

Cost: ~$0.30 per run × 365 ≈ $110/year (vs. Max subscription which is $200/year flat — Max wins if you also use claude.ai chat).

## Add Jenkins / SonarQube tokens for deeper monitoring

Day 1 the report will show "Jenkins DEFERRED — needs internal auth" because Jenkins itself requires basic-auth even on internal port. To fix:

1. Jenkins → admin user → Add API token. Save as `JENKINS_TOKEN` in `.env`.
2. SonarQube → My Account → Security → Generate Token (Global Analysis Token). Save as `SONAR_TOKEN`.
3. Add env passthrough in `docker-compose.ci-agent.yml`:
   ```yaml
   environment:
     - JENKINS_USER=admin
     - JENKINS_TOKEN=${JENKINS_TOKEN}
     - SONAR_TOKEN=${SONAR_TOKEN}
   ```
4. Update `templates/daily.md` health-check rows to use `-u admin:$JENKINS_TOKEN` and `-H "Authorization: Bearer $SONAR_TOKEN"` for the respective endpoints.

Now agent can rollup job color status + per-project quality gate results.
