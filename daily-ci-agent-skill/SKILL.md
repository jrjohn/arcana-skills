---
name: daily-ci-agent-skill
description: Deploy a containerized Claude CLI that runs daily on a self-hosted VPS — health-checks observability stack (Jenkins / SonarQube / Prometheus / Grafana / Loki / arch tools), reviews Renovate dependency PRs across GitHub org, checks image upgrade availability, and writes a markdown report served via authenticated nginx. Use when user wants to set up automated daily monitoring + dep updates on their own infra. Triggers: "daily-ci-agent", "daily CI report", "container claude cron", "Renovate review agent", "每日 CI 監測", "自動依賴更新監測 agent".
---

# daily-ci-agent skill

## What this skill does

Sets up a **Docker container running Claude CLI on cron** that every morning:

1. Reviews open Renovate Bot PRs across GitHub org → auto-merges safe patch/minor; flags major / SDK bumps; lists CI-failing
2. Health-checks 6+ services via internal docker network: Jenkins, SonarQube, Prometheus, Grafana, Loki, custom architecture-check tool (arch-qube)
3. Diffs running image tags against Docker Hub latest → flags pending upgrades
4. Writes markdown report to `/data/ci-reports/YYYY-MM-DD.md`
5. nginx serves the report behind Authelia 2FA at `https://<your-domain>/ci-reports/`

**Battle-tested on Rocky Linux 9 / aarch64 / Docker Compose v5+ / Authelia 4.39+ / nginx 1.20+.**

## When to invoke

- User asks to "set up daily monitoring agent" / "automate daily CI / SonarQube / Grafana checks"
- User wants to replicate this daily-ci-agent on their own VPS
- User mentions Renovate review automation across multi-repo org
- User wants Claude CLI to run unattended on cron in container

**Do NOT invoke for:**
- One-off health check (use direct curl)
- Single-repo dep update (Renovate alone is enough)
- Mac launchd cron (that's a different setup; this skill is Linux container + cron daemon)

## Files in this skill

```
SKILL.md                              ← you are here
templates/
  Dockerfile                          ← ubuntu:24.04 + claude CLI + gh + cron + claude-agent user
  docker-compose.ci-agent.yml         ← compose with volume, network, env
  entrypoint.sh                       ← chown + auto-restore .claude.json + start cron
  crontab                             ← `0 9 * * * root /usr/local/bin/daily-run.sh`
  daily-run.sh                        ← runuser → claude --print
  daily.md                            ← agent prompt (customize service list here)
scripts/
  setup-renovate.sh                   ← create renovate-config repo + PUT renovate.json across N repos
references/
  install-guide.md                    ← end-to-end setup walkthrough (~30 min)
  troubleshooting.md                  ← the 7 gotchas you WILL hit if you don't read this
  customization.md                    ← change cron / services / repos / report sink
```

## Quick start

```bash
# 1. Read references/install-guide.md (you'll hit at least 3 gotchas without it)
# 2. Copy templates/ to your VPS:
ssh <vps> mkdir -p /data/projects/daily-ci-agent /data/ci-reports
rsync -avz templates/ <vps>:/data/projects/daily-ci-agent/
# 3. Customize templates/daily.md (service hostnames, repo list)
# 4. Customize templates/docker-compose.ci-agent.yml (network name)
# 5. Add GH_TOKEN to .env on VPS, then:
ssh <vps> 'cd /data/projects/daily-ci-agent && docker compose -f docker-compose.ci-agent.yml --env-file .env up -d --build'
# 6. SSH into container shell + run `claude setup-token` (REQUIRED — see troubleshooting.md #1)
# 7. nginx + SELinux setup (see install-guide.md Phase D — DON'T skip the chcon step on Rocky/RHEL)
# 8. Install Renovate App on GitHub org → All repositories
# 9. Trigger manual test: `docker exec daily-ci-agent /usr/local/bin/daily-run.sh`
```

## Hard prerequisites

- VPS with Docker + Docker Compose v2+
- nginx in front with Authelia (or skip Authelia — adjust nginx block)
- Anthropic **Max** subscription on the account that will OAuth (Pro is rejected by inference API)
- GitHub PAT scope: `repo, workflow, read:org`
- An existing docker network the monitored services share (default in skill: `devops_default`)
- DNS pointing at the VPS for the public report URL

## Cost expectation

- Claude Max subscription bears all daily-agent token usage (no extra API billing)
- One run ≈ 5 min, ~30k input + ~5k output tokens
- Image / disk overhead: ~600 MB image, ~50 MB RAM idle, 1 MB / day report
