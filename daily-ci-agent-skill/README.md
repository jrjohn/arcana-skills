# daily-ci-agent-skill

Deploy a **containerized Claude CLI** that runs on cron in your self-hosted VPS, and every morning:

- Reviews open **Renovate Bot PRs** across your GitHub org → auto-merges safe patch/minor, flags major / SDK bumps, lists CI-failing
- Health-checks your observability stack (**Jenkins / SonarQube / Prometheus / Grafana / Loki**) via internal docker network
- Diffs running image tags vs Docker Hub latest → flags pending upgrades
- (Optional) Runs your **architecture-check tool** across all monitored repos
- Writes a markdown report to `/data/ci-reports/YYYY-MM-DD.md`
- Serves the report via authenticated nginx at `https://<your-domain>/ci-reports/`

## Why this skill exists

Setting this up from scratch involves ~10 non-obvious gotchas that each cost 15–30 min of debugging:

- Claude OAuth tokens are device-bound — Mac-issued tokens fail in Linux container
- `--dangerously-skip-permissions` refuses to run as `root`
- `useradd` / `runuser` / `cron` aren't in default PATH on `ubuntu:24.04` minimal
- `/root/.claude.json` lives OUTSIDE the volume mount target — gets wiped on recreate
- nginx `charset` directive doesn't apply to `text/markdown` — emoji/CJK become `??`
- SELinux on Rocky/RHEL blocks nginx serving `/data/`
- Authelia + Jenkins basic-auth = impossible to combine on a single request from outside the LAN

All distilled into `references/troubleshooting.md` with root cause + fix per gotcha.

## Structure

```
daily-ci-agent-skill/
├── SKILL.md                          # Triggers + quick overview
├── README.md                         # This file
├── templates/                        # Battle-tested artifacts to copy onto VPS
│   ├── Dockerfile                    # ubuntu:24.04 + claude CLI + gh + cron + non-root user
│   ├── docker-compose.ci-agent.yml
│   ├── entrypoint.sh                 # chown + auto-restore .claude.json + cron
│   ├── crontab                       # 0 9 * * * daily-run.sh
│   ├── daily-run.sh                  # runuser → claude --print
│   └── daily.md                      # The agent prompt (customize service list, repos)
├── scripts/
│   └── setup-renovate.sh             # Create central renovate-config repo + PUT renovate.json into N repos
└── references/
    ├── install-guide.md              # 7-phase end-to-end setup (~30 min)
    ├── troubleshooting.md            # 10 gotchas + root cause + fix
    └── customization.md              # Cron / services / repos / report sink variants
```

## Prerequisites

- VPS with Docker + Docker Compose v2+
- nginx (recommended: with Authelia for 2FA) in front
- **Anthropic Max** subscription (Pro is rejected by Claude Code inference API)
- GitHub PAT scope `repo, workflow, read:org`
- An existing docker network where your monitored services live (default: `devops_default`)
- DNS routes `<your-domain>/ci-reports/` to the VPS nginx

## Quick start

```bash
# Install the skill
curl -fsSL https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.sh | bash

# In Claude Code, trigger:
/daily-ci-agent-skill
# or just describe:
# "set up daily-ci-agent on my VPS"
```

Then follow `references/install-guide.md` for the 7-phase walkthrough.

**Critically: read `references/troubleshooting.md` first.** It will save you 2–3 hours of debugging.

## Cost / Maintenance

- **Cost**: One run ≈ 5 min, ~30k input + ~5k output token. Covered by Anthropic Max subscription if you OAuth.
- **OAuth refresh**: every ~60 days, interactive in container. Daily report warns 7 days before expiry.
- **GitHub PAT**: rotates per your org's policy. Update `.env` + restart container.
- **Renovate config tweak**: edit the central `<org>/renovate-config/default.json` repo; all monitored repos auto-pickup.

## Verified environments

- Rocky Linux 9 / aarch64
- Docker Compose v5.0.2
- Authelia 4.39.19
- nginx 1.20.1
- Claude Code 2.1.144

Other Linux + nginx combos should work with minor adjustments (SELinux step is Rocky/RHEL/CentOS-specific — skip on Debian/Ubuntu hosts).

## License

Same as the parent [arcana-skills](https://github.com/jrjohn/arcana-skills) repo.
