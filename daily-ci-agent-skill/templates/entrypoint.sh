#!/usr/bin/env bash
# Container entrypoint: configure runtime auth + start cron + tail log.
set -e

export PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin

# 1. Wire GitHub PAT into gh CLI (env var -> ~/.config/gh)
if [ -n "${GH_TOKEN:-}" ]; then
  if echo "$GH_TOKEN" | gh auth login --with-token 2>/tmp/gh_login.err; then
    echo "[entrypoint] gh authenticated as $(gh api user --jq .login 2>/dev/null || echo '?')"
  else
    echo "[entrypoint] WARN: gh auth login failed: $(cat /tmp/gh_login.err)"
  fi
else
  echo "[entrypoint] WARN: GH_TOKEN env not set; Renovate PR review will be skipped"
fi

# 2. Claude OAuth bootstrap check + chown for claude-agent (non-root) access
if [ ! -f /root/.claude/.credentials.json ]; then
  echo "[entrypoint] Claude CLI not yet authenticated."
  echo "[entrypoint] Run ONCE inside container shell:"
  echo "[entrypoint]   docker exec -it daily-ci-agent bash"
  echo "[entrypoint]   then: claude setup-token (or just: claude)"
else
  echo "[entrypoint] Claude credentials present at /root/.claude/.credentials.json"
fi

# Auto-restore /root/.claude.json from latest backup if missing (it lives outside volume mount)
if [ ! -f /root/.claude.json ] && [ -d /root/.claude/backups ]; then
  LATEST_BAK=$(ls -t /root/.claude/backups/.claude.json.backup.* 2>/dev/null | head -1)
  if [ -n "$LATEST_BAK" ]; then
    cp "$LATEST_BAK" /root/.claude.json
    echo "[entrypoint] restored /root/.claude.json from $LATEST_BAK"
  fi
fi

# chown the whole .claude dir + .claude.json so claude-agent can read/write
chown -R claude-agent:claude-agent /root/.claude /root/.claude.json 2>/dev/null || true
chmod 755 /root  # ensure claude-agent can traverse /root
chown -R claude-agent:claude-agent /data/ci-reports 2>/dev/null || true

# 3. Start cron + tail log forever (container stays up; cron fires daily)
CRON_BIN=$(command -v cron || echo /usr/sbin/cron)
"$CRON_BIN"
echo "[entrypoint] cron started ($CRON_BIN); tailing /var/log/daily-run.log"
exec tail -F /var/log/daily-run.log
