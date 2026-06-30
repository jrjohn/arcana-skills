# Cloud / Container Deployment

Walk-through for wiring `claude-session-archive-skill` inside a containerized Claude CLI (e.g. self-hosted VPS cron agent like `daily-ci-agent`). Mac / Linux dev-machine install lives in `installation-guide.md` — read that first if you haven't done a local install.

## When to use this guide

You're installing the archive into a Claude CLI that:

- Runs in a Docker container (not a human's dev machine)
- Is unattended (cron / systemd) — no interactive shell on each invoke
- Has Ollama in a sibling container reachable by Docker DNS, **not** localhost
- Shares a PostgreSQL instance with other Claude CLI clients (cross-machine archive)
- Has bind-mounted `~/.claude/` to host filesystem (so skills + sessions persist)

Confirmed working on Rocky Linux 9 aarch64 / Ubuntu 24.04 / Docker Compose v2+.

## Prerequisites

```bash
# Inside the container — verify before starting
which cargo                       # need Rust toolchain
which jq                          # need jq for settings.json merge
echo $OLLAMA_HOST                 # need http://<ollama-container>:11434
echo $CRS_PG_URL                  # need postgres://user:pw@host:5432/db?sslmode=...
getent hosts ollama               # DNS resolves
getent hosts <pg-container-name>  # DNS resolves
```

If `OLLAMA_HOST` / `CRS_PG_URL` are missing, set them in `docker-compose.yml` `environment:` block and recreate the container — env baked at start is much cleaner than runtime `export`.

## Architecture differences vs local

| Aspect | Local (Mac / Linux dev) | Cloud / Container |
|---|---|---|
| Ollama URL | `http://localhost:11434` (default) | `http://<container-dns>:11434` via `OLLAMA_HOST` env (since v1.17.1) |
| Scheduler | launchd / systemd timer | `cron.d` (container already has cron daemon) |
| pgsearchd daemon | Yes — unix socket saves ~700ms TLS handshake per query | **Skip** — same-host Docker network is already low-latency LAN (~5ms) |
| Sentinel file | `/tmp/claude-archive-preflight-<session>` | Same — `/tmp` is per-container, no collision |
| Memory grep hook | Active — many user memory files | Usually skipped — cron agents rarely have `~/.claude/projects/*/memory/` |
| Archive DB | Often local sqlite or remote PG over WAN | Usually same-host PG container (LAN, no TLS needed) |
| CLAUDE.md content | Personal profile + project context | Agent identity + hard constraints + sub-agent rules — see `templates/CLAUDE.md.cloud-agent.template` |

## Install — manual walkthrough

Each step has a "**why**" so you can decide whether to skip / adapt.

### 1. Get the skill into the container

If `~/.claude/` is bind-mounted, just rsync from host:

```bash
# On host
rsync -az --exclude='scripts/crs/target' /path/to/arcana-skills/claude-session-archive-skill/ \
  /data/<your-container>/claude-home/skills/claude-session-archive-skill/
chown -R 1001:1001 /data/<your-container>/claude-home/skills/claude-session-archive-skill/
# (1001 = claude-agent UID; adjust to your container's user)
```

**Why exclude target/**: rsyncing Mac build artifacts to aarch64 Linux is pointless — they won't run and balloon transfer size (~170MB → 456KB without `target/`).

### 2. Build `crs` inside the container

```bash
docker exec <container> bash -c "
  cd /root/.claude/skills/claude-session-archive-skill/scripts/crs && \
  cargo build --release --features pg-backend
"
# ~2 min on aarch64; produces target/release/crs
```

**Why pg-backend feature**: Cloud agents always use shared PG (cross-machine archive). Without this flag, `crs` falls back to local sqlite which defeats the point.

### 3. Symlink binary to PATH + create archive dir

```bash
docker exec <container> bash -c "
  ln -sf /root/.claude/skills/claude-session-archive-skill/scripts/crs/target/release/crs /usr/local/bin/crs
  mkdir -p /root/claude-archive
  chown -R claude-agent:claude-agent /root/claude-archive
"
```

**Why `/root/claude-archive`**: this is what `gen-recent` (SessionStart hook) writes context to. Even though pg-backend skips the sqlite path, the dir is still expected.

### 4. Install hooks

```bash
docker cp <skill>/scripts/archive-preflight.sh <container>:/root/.claude/hooks/
docker cp <skill>/scripts/auto-osearch-on-prompt.sh <container>:/root/.claude/hooks/
docker exec <container> chmod +x /root/.claude/hooks/*.sh
```

### 5. Register hooks in `~/.claude/settings.json`

Either edit by hand (only 4 entries needed — see `scripts/install.sh` for the jq merge logic) or run the helper:

```bash
docker exec <container> /root/.claude/skills/claude-session-archive-skill/scripts/install-container.sh \
  --skip-build --skip-cron --register-hooks-only
```

(Idempotent — safe to re-run.)

### 6. Install ingest cron

```bash
docker cp <skill>/templates/crs-build.cron <container>:/etc/cron.d/crs-build
docker exec <container> bash -c "
  # Set perms (cron rejects non-root-owned / writable cron.d files)
  chmod 0644 /etc/cron.d/crs-build
  chown root:root /etc/cron.d/crs-build
  # Log file owned by the user that runs the job
  touch /root/claude-archive/crs-build.log
  chown claude-agent:claude-agent /root/claude-archive/crs-build.log
"
```

**Edit `crs-build.cron` first** to set the right env vars — cron jobs don't inherit shell environment, the `OLLAMA_HOST` / `CRS_PG_URL` lines in the cron file are mandatory.

### 7. First-run backfill

```bash
docker exec -d -u claude-agent <container> bash -c "
  HOME=/root /usr/local/bin/crs build > /root/claude-archive/crs-build.log 2>&1
"
# Monitor with: docker exec <container> tail -f /root/claude-archive/crs-build.log
```

Backfill = ingest existing `~/.claude/projects/*/*.jsonl` + embed missing rows. With 8 parallel embed workers, expect ~150ms × (unembedded rows). 1500 rows ≈ 30 sec; 30000 rows ≈ 10 min.

### 8. Verify

```bash
docker exec <container> crs doctor
docker exec <container> crs vsearch '<concept your agent has logged>'
```

Expected `crs doctor` output for a healthy cloud install:

- ✓ archive dir exists
- ✗ db missing: sessions.db — **EXPECTED** (pg-backend, no sqlite)
- ✗ cron: no entry for crs build — **only if you didn't do step 6**
- ✓ hooks: SessionStart hook present
- ✓ ollama daemon reachable
- ✓ pg config: env vars present
- ✓ pg connect: SELECT 1 succeeded
- ⚠ pgsearchd socket missing — **EXPECTED** (cloud uses direct PG, daemon unnecessary)

The two `✗` and one `⚠` above are normal for cloud — don't try to "fix" them.

### 9. Deploy your agent's CLAUDE.md

Copy `templates/CLAUDE.md.cloud-agent.template` to `~/.claude/CLAUDE.md` in the container's claude-home and customize the marked placeholders. This is what every sub-agent (Task tool) inherits.

## Gotchas (battle-tested 2026-05-21)

These are real failure modes — read them before you hit them yourself.

### `cp: cannot create regular file '...crs': Text file busy`

You can't overwrite a running binary on Linux. If you're replacing `crs` while a `crs build` is mid-flight, `cp` fails with this error.

```bash
# Kill running crs by basename (NOT pkill -f, see next gotcha):
killall -TERM crs
sleep 2  # let it cleanup
cp new-crs /usr/local/bin/crs
```

### `pkill -f "crs build"` kills its own shell

`pkill -f` matches the **full command line** of every process. The shell running `pkill -f "crs build"` has `"crs build"` *in its own cmdline*, so it matches itself first and dies.

Use `killall <basename>` (matches binary name only, not cmdline) or pgrep + grep -v for self-filter.

### Defunct `[crs] <defunct>` zombies after kill

Containers usually don't run a proper init that reaps SIGCHLD. Killed crs processes become zombies that linger until the container restarts. Harmless but noisy in `ps`. To clean: restart the container, or pid-1 your container with `tini` (modify the Dockerfile to use `ENTRYPOINT ["/usr/bin/tini", "--"]`).

### vsearch project filter with leading dash

```bash
crs vsearch 'query' -root        # ❌ clap parses -root as an unknown flag
crs vsearch 'query' root         # ✅ LIKE %root% still matches '-root' project
crs vsearch 'query' -- -root     # ✅ -- terminates flag parsing
```

### `crs doctor` says "reachable at localhost:11434"

That string is a hardcoded label in the doctor output, **not** a measurement of the configured endpoint. Even after `OLLAMA_HOST` env override (v1.17.1+) makes embeds go to the right place, the doctor line still reads "localhost:11434". Don't be fooled. Verify by `crs vsearch 'anything'` and watching for the error vs. results.

### Shell `&&` over ssh + docker exec quoting hell

`ssh host 'sudo docker exec container bash -c "..."'` is three levels of quoting. Single quotes break inside, double quotes get re-expanded. For multi-line scripts: write the script to a local file, `scp` it over, `docker cp` it in, then `docker exec bash /tmp/script.sh`. Saved cumulative hours during the bluesea wiring.

### Container time zone vs cron schedule

`*/15 * * * *` fires every 15 min in **container TZ**. Ubuntu default is UTC; you probably want `TZ=Asia/Taipei` or your local zone set in `docker-compose.yml`. Otherwise reports timestamp in UTC, schedule fires at UTC :00 :15 :30 :45 — possibly fine but check.

### Ollama "Stopping..." cascade — cron stacking + memory + KEEP_ALIVE

**Symptom**: `top` shows ollama at 200%+ CPU and double-digit cumulative hours, but `ollama ps` says model is `"Stopping..."`. `vsearch` returns nothing. `docker logs ollama` is full of `aborting embedding request due to client closing the connection` at 60s intervals. Inside the daily-ci-agent container, `ps auxf` shows multiple `[crs] <defunct>` zombies plus 5–10 stacked `crs build` cron invocations.

**Root cause cascade** (production bluesea, 2026-05-25):

1. `crs build` cron fires every 15 min but a slow build runs >15 min (Ollama embed backlog, network blip, etc.). Cron has no overlap protection by default → second/third/fourth invocations stack.
2. All those `crs build` processes hammer Ollama embed in parallel.
3. Ollama container's memory limit (often 2 GB out of the box) is too tight: `bge-m3` model is 1.1 GB itself, plus per-request inference state. Memory pressure trips Ollama into trying to unload the model.
4. Default `OLLAMA_KEEP_ALIVE=5m` makes the model also try to unload on its own idle timer if any pause occurs.
5. With in-flight requests pinned to the model, the unload hangs → state stuck at `"Stopping..."` forever → all new requests time out at the client side (60s default) → daemons retry → more pressure.

**Fix** (apply all three):

```bash
# 1. cron stacking + parallelism cap — see templates/crs-build.cron
#    --workers 2 is the critical bit: crs default is 8 parallel embed
#    workers, which on a CPU-only ARM host with bge-m3 (~340ms / embed)
#    overwhelms Ollama and recreates the cascade even with the other
#    three fixes in place.
*/15 * * * * claude-agent /usr/bin/flock -n /tmp/crs-build.lock \
    /usr/local/bin/crs build --workers 2 >> ... 2>&1

# 2. Ollama docker-compose service — keep model loaded, give it headroom
services:
  ollama:
    environment:
      - OLLAMA_KEEP_ALIVE=-1  # model stays resident; no idle unload
    deploy:
      resources:
        limits:
          memory: 4G          # 2G is too tight for bge-m3 + concurrent embeds

# 3. Apply: docker compose up -d ollama
```

**Why --workers 2 matters more than you'd expect**: a single CPU-bound bge-m3 embed takes ~340ms once the model is warm. With `--workers 8` (default), `crs build` opens 8 concurrent embed requests; each gets a fraction of the CPU and serialises behind the others inside Ollama's runner. End-to-end latency per request climbs past 60s → client (crs) hits its 60s timeout → marks request as `err=error sending request` → retries → backlog grows faster than it drains. `--workers 2` keeps per-request latency under the client timeout. Bump higher only with measured headroom (e.g. Ollama on GPU).

**Recovery from the stuck state**:

```bash
# kill stacked crs builds inside the agent container
sudo docker exec <agent-container> pkill -f "crs build"
# restart ollama to clear "Stopping..." state
sudo docker restart ollama
# verify: should respond fast (first embed ~10–15s for model load, then <500ms)
sudo docker exec <agent-container> curl -s -X POST http://ollama:11434/api/embed \
  -d '{"model":"bge-m3","input":"healthcheck"}' --max-time 30 -w '\nhttp=%{http_code} t=%{time_total}s\n' -o /dev/null
```

**Monitoring**: any of these is the alarm:
- `top` shows `ollama` CPU% pinned high for >10 min with no `vsearch` activity
- `sudo docker logs ollama --tail 50 | grep "aborting embedding"` returns multiple lines
- `sudo docker exec <agent-container> ps auxf | grep '<defunct>'` returns multiple zombies

### Container DNS for sibling Docker services

`getent hosts ollama` only works if the container is on the **same Docker network** as `ollama`. Multi-network containers (e.g. `daily-ci-agent` on `devops_default` + `zeroclaw_default`) work fine — sibling resolves on either network. But a container only on `bridge` (default) can't reach a container on a user-defined network. Inspect with:

```bash
docker inspect <container> --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{println}}{{end}}'
```

## Cross-machine archive sharing — design notes

When multiple Claude CLI clients (your Mac + cloud agent + maybe a CI runner) write to the same `archive_main` PG database, **every session everywhere becomes searchable from every client**. Real example: bluesea daily-ci-agent's `vsearch` can find the Mac dev's design decisions from 4 weeks ago. This is the killer feature, but think about:

1. **Trust boundary** — `archive_main` is shared, no row-level isolation. Anything you talk about on machine A is visible to all clients. Treat the DB like a personal log, not credential storage. For credentials, use a vault.

2. **Noise / privacy via `project` filter** — different clients should query the projects they're responsible for. The cloud agent's CLAUDE.md should enforce a project-filter discipline (see template) so agents don't accidentally query unrelated personal session content.

3. **Backup is single point of failure** — losing the PG = collective amnesia. Schedule `pg_dump` to off-host backup, alongside whatever else you back up.

4. **Embedding cost amortization** — each new row ≈ 150ms embed time. With many clients ingesting concurrently into the same DB, Ollama is the bottleneck if you have only one instance. For >5 clients, consider running Ollama on the same host as PG for LAN embed speed, and have remote clients lean on the daemon path.

5. **Embed/OCR work-stealing (`--project-prefix` is mandatory for shared PG)** — `crs build`'s post-ingest `embed-missing` and `ocr-missing` phases scan the *entire* `msg` table for unembedded rows by default. With shared PG, that means Mac Metal Ollama burns cycles on bluesea's container sessions, bluesea ARM Ollama tries (and fails — 60s timeout cascade) to embed Mac sessions, and ocr-missing prints noisy `JSONL not found: /root/.claude/projects/-Users-jrjohn-...` warnings every cron cycle because each host looks for the OTHER host's local jsonl. Use `--project-prefix=...` on every host:
   - Mac launchd wrapper: `crs build --project-prefix=-Users-jrjohn`
   - bluesea cron: `crs build --workers 1 --project-prefix=-root,-workspace-arcana-book`
   - Prefix is matched as `project LIKE prefix || '%'`, comma-separated for multiple. Search (vsearch/csearch) is unaffected — partition only constrains *write* workers.

6. **PG `tcp_keepalives_idle = 60`** (server-side) — without this, idle TCP between batch INSERTs gets evicted by intermediate NAT (home router, FortiGate, ISP CGN, cloud SLB) and `crs build` hangs forever in `ESTABLISHED` state with no kernel-level detection until the 2-hour keepalive default. Set on the PG host (no client changes needed):
   ```sql
   ALTER SYSTEM SET tcp_keepalives_idle = 60;
   ALTER SYSTEM SET tcp_keepalives_interval = 10;
   ALTER SYSTEM SET tcp_keepalives_count = 6;
   SELECT pg_reload_conf();
   ```
   Verify with a fresh **TCP** connection (`psql -h 127.0.0.1`); Unix-socket sessions always read 0 per PG docs — that's not a bug.

## Next steps after install

- Edit `templates/CLAUDE.md.cloud-agent.template` and drop into your container's claude-home as `CLAUDE.md`
- Tune cron frequency (`*/15` works for low-volume agents; `*/5` for chattier ones)
- (Optional) Wire `pg_dump` cron on the PG host for daily backup
- (Optional) Add `gen-recent` SessionStart hook so each new agent session sees recent context auto-injected (already wired by default — see existing settings.json)
