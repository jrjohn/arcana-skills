# daily-ci-agent troubleshooting — the 8 gotchas you WILL hit

Distilled from actually building this from scratch (~3 hours of debugging compressed into "do these things and skip the pain"). Read this BEFORE install-guide.md.

---

## #1: Claude OAuth `setup-token` from Mac does NOT work in Linux container

**Symptom**: You run `claude setup-token` on Mac, get a token like `XXX#YYY`, paste it as `ANTHROPIC_AUTH_TOKEN` env in container, get `401 Invalid bearer token` from `claude --print`. `claude auth status` confusingly reports `loggedIn: true` but `subscriptionType: null, email: null, orgId: null`.

**Root cause**: OAuth tokens are device-fingerprinted by Anthropic. Mac-issued tokens are rejected when used from Linux container even with valid format.

**Fix**: Run the OAuth flow **inside the container, interactively, from a real TTY all the way down**. The sequence:

1. From Mac Terminal.app (NOT Claude Code's `!` sub-shell — it doesn't allocate TTY through SSH):
   ```bash
   ssh -t vps                                  # -t allocates remote pty
   docker exec -it daily-ci-agent bash         # -it allocates container pty
   claude                                      # interactive — NOT setup-token alone
   ```
2. Follow device-code URL, authorize in browser.
3. Exit `/exit`, exit shells.

**Why interactive `claude` not `setup-token`**: bare `setup-token` only writes a stub `.credentials.json` with empty subscription metadata. Interactive `claude` triggers the FULL OAuth handshake including subscription discovery, and writes a complete credentials file. The 401 we hit was Anthropic rejecting the stub-token because subscription metadata was missing.

**Verify after**: `claude auth status` should show `subscriptionType: "max"`, `email: "<your-email>"`, `orgId: "<uuid>"`. If still null → re-run interactive `claude`.

---

## #2: `--dangerously-skip-permissions` refuses to run as root

**Symptom**: Container runs as root (Docker default). When daily-run.sh invokes `claude --print --dangerously-skip-permissions`, you get:
```
--dangerously-skip-permissions cannot be used with root/sudo privileges for security reasons
```

**Root cause**: Anthropic's Claude Code security policy. Reasonable — `--dangerously-skip-permissions` lets the agent run arbitrary Bash; as root that's catastrophic.

**Fix**: Create a non-root user in the image + run `claude` as that user via `runuser`:

```dockerfile
# Dockerfile
RUN /usr/sbin/useradd -M -d /root -s /bin/bash claude-agent
```

```bash
# daily-run.sh
/usr/sbin/runuser -u claude-agent -- env HOME=/root REPORT_PATH="$REPORT_PATH" \
  claude --print --dangerously-skip-permissions "$PROMPT_CONTENT"
```

**Critical detail**: `claude-agent`'s HOME must be `/root` so it reads the same `~/.claude/.credentials.json` you OAuth'd into. The entrypoint must `chown -R claude-agent:claude-agent /root/.claude /root/.claude.json` so the non-root user can read them.

---

## #3: `useradd` / `runuser` not in PATH at build time

**Symptom**: `docker build` fails with `useradd: command not found` (exit 127). Or container starts but `daily-run.sh` errors `runuser: command not found`.

**Root cause**: `ubuntu:24.04` minimal image doesn't have `/usr/sbin/` in `/bin/sh`'s PATH at build time. And `runuser` is in package `util-linux` which may or may not be in minimal install.

**Fix**: Two things in Dockerfile:

1. Install both packages explicitly:
   ```dockerfile
   RUN apt-get update && apt-get install -y --no-install-recommends \
       ... passwd util-linux \
       ...
   ```
2. Use absolute paths:
   ```dockerfile
   RUN /usr/sbin/useradd -M -d /root -s /bin/bash claude-agent
   ```
   And in daily-run.sh: `/usr/sbin/runuser -u claude-agent -- ...`

---

## #4: `/root/.claude.json` lives OUTSIDE the volume mount

**Symptom**: Container restart wipes `claude` config. You see `Claude configuration file not found at: /root/.claude.json` even though you mounted `/root/.claude` as a persistent volume.

**Root cause**: The volume mount target `/root/.claude/` is a directory; `/root/.claude.json` is a sibling file at `/root/` level — NOT inside the mount, so it's part of the container layer and gets wiped on recreate.

**Fix**: Entrypoint auto-restores from latest backup. Claude Code keeps backups in `/root/.claude/backups/.claude.json.backup.<epoch>` inside the volume. Add to entrypoint:

```bash
if [ ! -f /root/.claude.json ] && [ -d /root/.claude/backups ]; then
  LATEST_BAK=$(ls -t /root/.claude/backups/.claude.json.backup.* 2>/dev/null | head -1)
  [ -n "$LATEST_BAK" ] && cp "$LATEST_BAK" /root/.claude.json
fi
```

(Don't mount the whole `/root` as volume — that breaks too much else.)

---

## #5: `cron` not in PATH for entrypoint script

**Symptom**: Container restart-loops with `[entrypoint] cron: command not found` in logs.

**Root cause**: `cron` binary is at `/usr/sbin/cron`. Container's default PATH doesn't include `/usr/sbin/`. (Yes — same family of bug as #3.)

**Fix**: In entrypoint:

```bash
export PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
CRON_BIN=$(command -v cron || echo /usr/sbin/cron)
"$CRON_BIN"
```

---

## #6: nginx `charset utf-8` does NOT apply to `text/markdown` by default

**Symptom**: Browser shows `??` instead of emoji (`⚠️`) or Chinese in `.md` reports. nginx response header is `Content-Type: text/markdown` with no charset.

**Root cause**: nginx's `charset` directive only adds `; charset=utf-8` to MIME types in `charset_types`. Default list is `text/html text/xml text/plain text/vnd.wap.wml application/javascript application/rss+xml` — **does NOT include `text/markdown`**.

**Fix**: In your `location /ci-reports/` block, add:

```nginx
charset utf-8;
charset_types text/markdown text/plain text/html application/json;
```

Verify: `curl -I https://your-domain/ci-reports/X.md | grep -i content-type` should show `text/markdown; charset=utf-8`.

---

## #7: SELinux on Rocky / RHEL / CentOS blocks nginx from serving `/data/`

**Symptom**: nginx returns 403 Forbidden even though file perms look fine. `tail /var/log/nginx/error.log` shows `Permission denied` on opendir/open.

**Root cause**: SELinux is `Enforcing`. `/data/ci-reports/` has context `unlabeled_t`. nginx needs `httpd_sys_content_t` to read it.

**Fix**:
```bash
sudo semanage fcontext -a -t httpd_sys_content_t "/data/ci-reports(/.*)?"
sudo restorecon -Rv /data/ci-reports/
```

The `semanage fcontext` line is **permanent** — new files added under `/data/ci-reports/` automatically get the right label. Without it you'd need to re-`chcon` every new daily report.

Verify: `ls -laZ /data/ci-reports/` should show `httpd_sys_content_t`.

---

## #8: Authelia + Jenkins basic auth — cannot coexist on a single request

**Symptom**: From an external client (your Mac, GitHub Actions, etc), you try to call `https://<domain>/jenkins/api/json` with `Authorization: Basic <jenkins_user>:<token>` and a valid Authelia session cookie. You get HTTP 302 redirecting to Authelia login page.

**Root cause**: Authelia's `auth_request` handler intercepts ANY incoming `Authorization` header to validate against Authelia's own user store. If it doesn't match an Authelia user, it rejects (302) — IGNORING your session cookie.

There is NO client-side workaround. Tested combinations all fail:
- cookie + `Authorization: Basic <jenkins>` → 302
- cookie + `Authorization: Bearer <jenkins>` → blocked (classifier flagged probing too)
- form-login to Jenkins for JSESSIONID → Jenkins's login form rejects API tokens as password
- cookie + Authelia user creds in basic-auth (when same user exists in both) → still 302 because Authelia doesn't pass-through the header to Jenkins after validating

**Three real fixes** (pick one, all require server-side change):

A. **Skip Authelia entirely from inside the docker network**. THIS IS THE FIX USED IN THIS SKILL. The daily-ci-agent runs as a container ON `devops_default`, hits `http://jenkins:8080/jenkins/api/json` directly (no public hostname, no Authelia). Internal-only auth.

B. Install Jenkins **Reverse Proxy Auth plugin** + nginx `proxy_set_header Remote-User $remote_user`. Cookie-only flow; Jenkins trusts Authelia's user identity. Heavier setup but lets external clients reach via public URL.

C. nginx config: for `/jenkins/api/` specifically, set `auth_request_set` such that Authorization header is preserved and passed to Jenkins (not consumed by Authelia). Hacky and requires deep nginx + auth_request knowledge.

**Implication for this skill**: daily-ci-agent MUST run in container ON the same docker network as the services it monitors. Running it from Mac or external host = won't work for Authelia-protected services.

---

## #9 (minor): `gh auth login --with-token` warns when GH_TOKEN env is set

**Symptom**: entrypoint log says `WARN: gh auth login failed: The value of the GH_TOKEN environment variable is being used for authentication. To have GitHub CLI store credentials instead, first clear the value from the environment.`

**Reality**: This is NOT a failure. When `GH_TOKEN` env is set, `gh` uses it directly and refuses to write to `~/.config/gh/`. The token IS being used. Verify with `gh auth status` — should show `Logged in to github.com account <name> (GH_TOKEN)`.

**Fix**: Nothing. Ignore the warning, or update entrypoint to suppress it gracefully.

---

## #10 (cosmetic): Mend onboarding dashboard 404

**Symptom**: After installing Renovate App and clicking through the Mend onboarding wizard, you land on a 404 "this organization is not onboarded".

**Reality**: Cosmetic only. The GitHub App is installed regardless. Verify at https://github.com/settings/installations — `Renovate` should be listed. The Mend dashboard is their commercial product and 404s for orgs not on a paid Mend plan. You don't need it.

---

## #11: agent's `vsearch`/`csearch` archive lookup fails — usually PATH, sometimes a dead project label

If you wired the agent to the shared archive (see `claude-session-archive-skill` → `references/cloud-deployment.md`), the agent's own archive-first lookup can still fail two ways:

**(a) `vsearch: command not found` even though `crs` + creds are present.** The self-contained wrappers (`~/.claude/bin/{vsearch,csearch}`, each `export CRS_PG_URL="$(cat ~/.claude/.crs_pg_url)"; export OLLAMA_HOST=http://ollama:11434; exec crs vsearch "$@"`) and `.crs_pg_url` are mounted, but `~/.claude/bin` is **not on the container's PATH** — so bare `vsearch`/`csearch` resolve to nothing while `/root/.claude/bin/csearch` works by full path. Fix: prepend `~/.claude/bin` to a **full** explicit `PATH=` in the agent's env-file (env-file PATH replaces the image's — list every existing dir). Diagnose with `docker exec <agent> command -v csearch` FIRST: "not found" = PATH, not creds/Ollama. No image rebuild needed.

**(b) `vsearch '...' <project>` returns empty.** The agent's CLAUDE.md project-filter allow-list points at a label with **0 rows**. If the agent's own AI-task transcripts are ingested under `project='aaf'` (via the BPMN worker — see `arcana-ai-agent-flow-skill` §6.1) but the allow-list still says `daily-ci-agent` (a dead label), every filtered search returns nothing. Fix: set the allow-list project to the label the runs are actually stored under (`aaf`). Keep the deny-list (Somnics/medical/personal-Mac paths) intact — global queries stay forbidden for credential/PII protection. CLAUDE.md is re-read per headless `claude` invocation (mounted), so no restart.

---

## Debugging recipe (when something inexplicably fails)

1. Container logs: `docker logs daily-ci-agent | tail -50`
2. Daily run log: `docker exec daily-ci-agent tail -50 /var/log/daily-run.log`
3. Today's report (or error stub): `cat /data/ci-reports/$(date +%F).md`
4. Container shell for live poking: `docker exec -it daily-ci-agent bash`
5. Test claude as agent-user without cron: `/usr/sbin/runuser -u claude-agent -- env HOME=/root claude --print --dangerously-skip-permissions "say ok"`
6. Test gh: `docker exec daily-ci-agent gh auth status`
7. Test internal service reachability: `docker exec daily-ci-agent curl -sS http://prometheus:9090/-/healthy`
