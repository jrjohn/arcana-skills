# daily-ci-agent install guide

End-to-end setup, ~30 minutes if you follow this exactly. If you start improvising you'll hit one or more of the gotchas in `troubleshooting.md` — **read that file first** so you know what's coming.

## Prerequisites checklist

- [ ] SSH access to VPS (e.g. `ssh <your-vps>`)
- [ ] Docker + Docker Compose v2+ on VPS (`docker compose version`)
- [ ] nginx in front + (optional) Authelia for 2FA
- [ ] An existing docker network where the monitored services live (typically `devops_default` — check with `ssh vps 'docker network ls | grep default'`)
- [ ] Anthropic **Max** subscription (Pro tier rejected by inference API)
- [ ] GitHub PAT with scopes `repo, workflow, read:org` (classic, no expiry)
- [ ] DNS / proxy already routes `<your-domain>/ci-reports/` to the VPS nginx

If any are missing, stop and provision them first.

---

## Phase A — Container build on VPS (10 min)

1. **Create directories on VPS** (run as a user with `sudo`):
   ```bash
   ssh vps 'sudo mkdir -p /data/projects/daily-ci-agent /data/ci-reports && sudo chown -R $(whoami):$(whoami) /data/projects/daily-ci-agent /data/ci-reports'
   ```

2. **Copy skill `templates/` to VPS**:
   ```bash
   cd ~/.claude/skills/daily-ci-agent
   rsync -avz templates/ vps:/data/projects/daily-ci-agent/
   ```

3. **Customize `templates/daily.md` (the agent prompt)** before deploy:
   - Update the **service health matrix** — internal hostnames + healthy criteria for YOUR stack
   - Update the **repo list** (`<YOUR-ORG>` and target repos) in Renovate PR review section
   - Update the **image tags to track** in image upgrade check

4. **Customize `templates/docker-compose.ci-agent.yml`**:
   - Change `networks.devops_default.external: true` to your actual network name
   - Adjust `TZ=Asia/Taipei` if needed

5. **Build + start container**:
   ```bash
   ssh vps 'cd /data/projects/daily-ci-agent && docker compose -f docker-compose.ci-agent.yml up -d --build'
   ```

6. **Verify container alive**:
   ```bash
   ssh vps 'docker ps --filter name=daily-ci-agent --format "{{.Names}}\t{{.Status}}"'
   # Expect: daily-ci-agent  Up X seconds (health: starting)
   ```

   Check logs: `ssh vps 'docker logs daily-ci-agent | tail -20'`. You should see:
   - `[entrypoint] WARN: GH_TOKEN env not set` (we add this in Phase C)
   - `[entrypoint] Claude CLI not yet authenticated.` (we do this in Phase B)
   - `[entrypoint] cron started (/usr/sbin/cron); tailing /var/log/daily-run.log`

   **If container restart-loops with `cron: command not found`** → you didn't rebuild after editing entrypoint. Force rebuild: `docker compose ... build --no-cache`.

---

## Phase B — Claude OAuth in container (5 min, INTERACTIVE)

⚠️ This step **must** be done from a real Terminal app (Mac Terminal.app / iTerm2 / etc.) — NOT from inside Claude Code's `!` shell, which doesn't allocate TTY end-to-end. See `troubleshooting.md` #1.

1. Open your terminal app.
2. SSH into VPS:
   ```bash
   ssh vps
   ```
3. Get a shell inside the container:
   ```bash
   docker exec -it daily-ci-agent bash
   ```
4. Run `claude` interactively (not `setup-token`):
   ```bash
   claude
   ```
   Even if you just want the token, run interactive `claude` first because it forces the full OAuth handshake and populates `subscriptionType`, `email`, `orgId` in `/root/.claude.json`. Just running `setup-token` leaves these null and the API returns 401.

5. The CLI prints a device-code URL like `https://anthropic.com/activate?code=ABCD-EFGH`. Open in browser, log in with your **Max-tier** Anthropic account, paste the code, authorize.
6. Back in the container shell: send a test message (e.g. `hi`), get response, then `/exit`.
7. **Verify auth**:
   ```bash
   # still inside container
   /usr/sbin/runuser -u claude-agent -- env HOME=/root claude auth status
   # expect: { "loggedIn": true, "authMethod": "claude.ai", "subscriptionType": "max", "email": "..." }
   ```
   `subscriptionType` MUST be `"max"`. If it's `null` or `"pro"`, daily-run will 401 — go upgrade your Anthropic plan.

8. Exit the container shell + SSH.

---

## Phase C — GitHub PAT (2 min)

1. Browser: https://github.com/settings/tokens/new → classic token → check `repo`, `workflow`, `read:org` → name `<your-vps>-daily-ci-agent` → no expiration → Generate → copy `ghp_...`.

2. Write into VPS `.env`:
   ```bash
   ssh vps 'umask 077 && echo "GH_TOKEN=ghp_..." > /data/projects/daily-ci-agent/.env && chmod 600 /data/projects/daily-ci-agent/.env'
   ```

3. Restart container so it picks up new env:
   ```bash
   ssh vps 'cd /data/projects/daily-ci-agent && docker compose -f docker-compose.ci-agent.yml --env-file .env up -d --force-recreate'
   ```

4. Verify gh auth inside container:
   ```bash
   ssh vps 'docker exec daily-ci-agent gh auth status 2>&1 | head -5'
   # expect: ✓ Logged in to github.com account <yourname> (GH_TOKEN)
   ```

---

## Phase D — nginx + SELinux for public report URL (5 min)

1. **Add nginx location block.** Find your existing server block for the public domain. Insert this `location` block, modelled on your existing Authelia-protected blocks:

   ```nginx
   # CI reports — /ci-reports/ — daily-ci-agent output
   location /ci-reports/ {
       auth_request /internal/authelia/authz;
       auth_request_set $redirect $upstream_http_location;
       auth_request_set $user $upstream_http_remote_user;
       auth_request_set $groups $upstream_http_remote_groups;
       auth_request_set $name $upstream_http_remote_name;
       auth_request_set $email $upstream_http_remote_email;
       error_page 401 =302 https://<your-domain>/authelia/?rd=$scheme://$http_host$request_uri;

       alias /data/ci-reports/;
       autoindex on;
       autoindex_exact_size off;
       autoindex_localtime on;
       default_type text/plain;
       charset utf-8;
       charset_types text/markdown text/plain text/html application/json;
       types { text/markdown md; }
   }
   ```

   **Critical: the `charset_types` directive.** nginx's `charset` does NOT apply to `text/markdown` by default. Without it, emoji and Chinese characters in the report show as `??` in browser. See `troubleshooting.md` #6.

2. Test + reload:
   ```bash
   ssh vps 'sudo nginx -t && sudo systemctl reload nginx'
   ```

3. **SELinux fix (CRITICAL on Rocky / RHEL / CentOS)**. nginx serves `/data/ci-reports/` but SELinux blocks it by default because the dir lacks the `httpd_sys_content_t` context. You'll see `403 Forbidden` from browser and `Permission denied` in nginx error.log. Fix:

   ```bash
   ssh vps 'sudo semanage fcontext -a -t httpd_sys_content_t "/data/ci-reports(/.*)?" && sudo restorecon -Rv /data/ci-reports/'
   ```

   Verify: `ls -laZ /data/ci-reports/` should show `httpd_sys_content_t`.

4. Browser test: open `https://<your-domain>/ci-reports/` → Authelia login → after auth, see directory listing (empty until first report).

---

## Phase E — Renovate Bot setup (10 min)

1. **Create central Renovate config repo** (one-time, holds shared preset):
   ```bash
   ssh vps 'docker exec daily-ci-agent bash /opt/scripts/setup-renovate.sh'
   # OR adapt scripts/setup-renovate.sh from this skill — edit the REPOS=() list at line ~50 to match YOUR repos
   ```

   What it does: creates `<org>/renovate-config` with `default.json` (preset), PUTs `renovate.json` (single line `{"extends": ["github>org/renovate-config"]}`) into each repo in the list.

2. **Install Renovate GitHub App**:
   - Browser: https://github.com/apps/renovate → Install → choose your org → "All repositories" (simpler) or "Only select repositories" (prick each).
   - Mend Onboarding dashboard (if shown):
     - First page → choose **Renovate Only** (free; Mend Application Security is paid SCA/SAST you don't need)
     - Second page → choose **Scan and Alert** (NOT Scan Only — Scan Only sets Renovate to silent and never opens PRs)
     - If you hit a 404 after Save, ignore — the App is installed; verify at https://github.com/settings/installations.

3. **Verify**: https://github.com/settings/installations → "Renovate" with "All repositories" or your selected list. Within 5–30 minutes, Renovate scans all repos and opens initial dep-update PRs.

---

## Phase F — End-to-end test (3 min)

```bash
ssh vps 'docker exec daily-ci-agent /usr/local/bin/daily-run.sh'
# Watch: should print "result: report written to /data/ci-reports/YYYY-MM-DD.md"
# Takes 3–8 min depending on # services + repos
```

Check the file:
```bash
ssh vps 'head -40 /data/ci-reports/$(date +%F).md'
```

Open in browser: `https://<your-domain>/ci-reports/<today>.md` → expect Markdown text with `⚠️` and `─` showing correctly (UTF-8 working).

If anything fails, see `troubleshooting.md`.

---

## Phase G — Cron is already running

Cron daemon started by entrypoint. Default schedule: `0 9 * * * root /usr/local/bin/daily-run.sh` (09:00 local TZ).

To verify next fire: `ssh vps 'docker exec daily-ci-agent cat /etc/cron.d/daily-ci-agent'`.

To change time: edit `templates/crontab`, rebuild, restart container.

---

## What you should have at the end

- container `daily-ci-agent` Up, restart=unless-stopped
- `/data/ci-reports/` populated daily at 09:00
- `https://<your-domain>/ci-reports/` browsable behind 2FA
- Renovate Bot scanning all org repos, opening dep PRs
- Tomorrow's report shows Renovate review results + 6-service health + image upgrade list + action items

## Maintenance touchpoints

- **Claude OAuth token expires every ~60 days.** Re-run Phase B step 4 (interactive `claude` in container) before expiry. Report header warns 7 days before.
- **GH PAT rotation** (if you set expiry): re-do Phase C.
- **Renovate config tweaks**: edit `<org>/renovate-config/default.json`, push; all repos auto-pickup on next Renovate run.
- **Add new service to monitor**: edit `templates/daily.md`, rebuild image (`docker compose ... build && up -d --force-recreate`).
