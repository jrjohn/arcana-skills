# PostgreSQL + pgvector backend

The skill's default backend is local SQLite + sqlite-vec. The **PostgreSQL + pgvector** backend is for when you want **cross-device** access — query the same archive from any laptop, phone tunnel, or remote shell — at the cost of a TLS round-trip per query (~280-400ms warm via daemon vs sub-10ms local).

Same `crs` source supports both backends via a Cargo feature flag (`pg-backend`). Default `cargo build --release` produces a sqlite-only binary; `cargo build --release --features pg-backend` produces a PG-routed binary that adds the `pgsearch` / `pgsearchd` subcommands and re-routes `csearch` / `vsearch` / `vsearch-since` / `build` / `embed-missing` through PostgreSQL. The two builds are mutually exclusive at runtime (whichever you build determines the backend); switching is a 10-30s `cargo build`.

## When to use which

| Choose **sqlite** (default) if | Choose **PG+pgvector** if |
|---|---|
| Single device | Multi-device (laptop + iMac + remote shell) |
| Don't want a server | Already have a VPS / cloud box |
| Sub-10ms latency mandatory | OK with 280-400ms via daemon, ~1s direct |
| Privacy-paranoid (archive has credentials) | OK extending trust boundary to that server |

## Architecture

```
Mac (client)                          Internet                     Cloud VPS (server)
─────────────                         ────────                     ─────────────────
~/.claude/projects/*/*.jsonl
       │
       ▼  crs build (launchd 15min)
       │   incremental INSERT
       │
       ├──────────TLS────────────────────────────────────────►  pg-archive-test
       │                                                          (postgres:17+pgvector)
       │                                                            │
       ├──────────TLS────────────────────────────────────────►  msg table
       │   csearch / vsearch / vsearch-since                       (GIN + HNSW indexes)
       │
       └─►  pgsearchd (unix socket daemon)
              holds r2d2 pool size=4
              persistent TLS connections
              ~/Library/Caches/pgsearchd/pgsearchd.sock

network layers:
  ISP / corporate egress (e.g. FortiGate egress rule for tcp/5432)
  Cloud security list (e.g. OCI ingress whitelist 118.163.x.x/32 → tcp/5432)
  TLS cert: Let's Encrypt on your VPS hostname
```

## Server-side setup (one-time)

### 1. PG container with pgvector

```yaml
# /data/pg-archive/docker-compose.yml
services:
  pg:
    image: pgvector/pgvector:pg17
    container_name: pg-archive
    restart: unless-stopped
    env_file: .env
    environment:
      - POSTGRES_USER=archive
      - POSTGRES_DB=archive_main
    volumes:
      - ./data:/var/lib/postgresql/data:Z   # :Z for SELinux; drop on Ubuntu
    ports:
      - '0.0.0.0:5432:5432'                  # public bind, restrict via firewall
    command: >
      postgres
      -c ssl=on
      -c ssl_cert_file=/var/lib/postgresql/data/server.crt
      -c ssl_key_file=/var/lib/postgresql/data/server.key
```

```bash
# .env (chmod 600)
POSTGRES_PASSWORD=<32-char random>
```

### 2. TLS via Let's Encrypt

If you already have a cert for your hostname (e.g. from nginx), reuse it:

```bash
sudo cp -L /etc/letsencrypt/live/<your.domain>/fullchain.pem /data/pg-archive/data/server.crt
sudo cp -L /etc/letsencrypt/live/<your.domain>/privkey.pem  /data/pg-archive/data/server.key
sudo chown 999:999 /data/pg-archive/data/server.{crt,key}
sudo chmod 644 /data/pg-archive/data/server.crt
sudo chmod 600 /data/pg-archive/data/server.key
docker exec pg-archive psql -U archive -d postgres -c 'SELECT pg_reload_conf();'
```

**Renewal hook** (must do this — Let's Encrypt expires every 90 days):

```bash
# /etc/letsencrypt/renewal-hooks/deploy/sync-to-pg.sh
#!/bin/bash
DOMAIN=<your.domain>
TARGET=/data/pg-archive/data
cp -L /etc/letsencrypt/live/$DOMAIN/fullchain.pem $TARGET/server.crt
cp -L /etc/letsencrypt/live/$DOMAIN/privkey.pem $TARGET/server.key
chown 999:999 $TARGET/server.{crt,key}
chmod 600 $TARGET/server.key
docker exec pg-archive psql -U $POSTGRES_USER -d postgres -c 'SELECT pg_reload_conf();'
```

### 3. Create schema

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE msg (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL,
    project     TEXT NOT NULL,
    seq         INTEGER NOT NULL,
    ts          TIMESTAMPTZ,
    role        TEXT,
    tool_name   TEXT,
    content     TEXT,
    content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', COALESCE(content,''))) STORED,
    embedding   vector(1024),     -- bge-m3
    UNIQUE (session_id, seq)
);
CREATE INDEX msg_ts_idx       ON msg (ts);
CREATE INDEX msg_project_idx  ON msg (project, ts);
CREATE INDEX msg_tool_idx     ON msg (tool_name);
CREATE INDEX msg_tsv_idx      ON msg USING GIN  (content_tsv);
CREATE INDEX msg_emb_idx      ON msg USING hnsw (embedding vector_cosine_ops);

CREATE TABLE ingest_state (
    file_path TEXT PRIMARY KEY,
    mtime DOUBLE PRECISION NOT NULL,
    lines BIGINT NOT NULL
);
```

### 4. Network whitelist

Choose your stack:

| Layer | What to open |
|---|---|
| Cloud security list (AWS / OCI / GCP) | Ingress `<your home IP>/32 → tcp/5432` |
| OS firewall (firewalld / ufw / iptables) | Same — usually mirror cloud rule |
| Corporate egress (FortiGate / Cisco / Palo Alto) | Outbound tcp/5432 allowed from your office IP |

For dynamic home IPs: use a DDNS hostname instead, then either (a) refresh cloud rule via a cron, or (b) skip IP whitelist and rely on TLS + strong password + fail2ban.

## Client-side setup (each machine)

### 1. Build `crs` for PG mode

Connection details are read from env vars (no hardcoded credentials in the source — that would publish your password to whoever clones the repo). Either set `CRS_PG_URL` to a full libpq connection string, or set the components individually:

```bash
export CRS_PG_HOST=arcana.example.com
export CRS_PG_PORT=5432
export CRS_PG_USER=archive
export CRS_PG_DB=archive_main
export CRS_PG_PASSWORD='<the 32-char password>'
# OR (overrides all above):
export CRS_PG_URL='host=arcana.example.com port=5432 user=archive password=<...> dbname=archive_main sslmode=require'
```

`CRS_PG_PASSWORD` is **required** when feature is enabled — `crs` will refuse to start without it. The other components have safe defaults (`localhost` / `5432` / `archive` / `archive_main`).

Build:

```bash
cd ~/claude-archive/crs
cargo build --release --features pg-backend
# binary at target/release/crs — now has Pgsearch + Pgsearchd subcommands

# Or use the installer:
cd <skill>/scripts && ./install.sh --with-pg
```

Verify the build picked up the feature:

```bash
crs --help | grep pgsearch
# should list: pgsearch, pgsearchd
```

### 2. Daemon (avoids ~700ms TLS handshake per query)

The `pgsearchd` subcommand listens on `~/Library/Caches/pgsearchd/pgsearchd.sock` (chmod 600) and holds an r2d2 pool of pre-warmed TLS connections to PG. Every `csearch` / `vsearch` / `pgsearch` invocation auto-detects the socket and tunnels its query through it — saving the ~700ms TLS handshake on every run. Without the daemon each query reconnects fresh; the binary still works, just slower.

```bash
# Run foreground to test (Ctrl-C to stop)
crs pgsearchd

# launchd plist for KeepAlive on macOS — install.sh --with-pg writes this
# template into ~/Library/LaunchAgents/com.<USERNAME>.pgsearchd.plist:
#   <key>EnvironmentVariables</key><dict>
#     <key>CRS_PG_HOST</key><string>arcana.example.com</string>
#     <key>CRS_PG_PASSWORD</key><string>...</string>
#   </dict>
# Edit the placeholders, then:
launchctl load ~/Library/LaunchAgents/com.<USERNAME>.pgsearchd.plist
```

Daemon listens on `$XDG_CACHE_HOME/pgsearchd/pgsearchd.sock` (defaults to `~/Library/Caches/...` on macOS, `~/.cache/...` on Linux), chmod 600.

### 3. Build cron (same plist as sqlite — re-points to PG-built binary)

`com.<USERNAME>.claude-archive.plist` runs `crs build` every 15 min. When `crs` is built with `--features pg-backend`, that subcommand writes to PG instead of local sqlite — same plist, different binary behavior.

### 4. Initial seed

Two paths:

**A. From scratch** (no prior sqlite archive): just let `crs build` run via cron. Will start from empty, ingest current jsonl files. Slow first time (~10 rows/sec via TLS) but only matters first run.

**B. Migrate from existing sqlite** (recommended if you have months of data):

```bash
# 1. scp sessions.db to server
rsync -avP ~/claude-archive/sessions.db <server>:/data/pg-archive/import/

# 2. Run migration script on server (faster than streaming over network)
#    Reads sqlite locally, INSERTs to local PG over docker-proxy.
#    Script: see references/pg-migration.py (handles NUL bytes + bad ts + 1024d vec decode)
ssh <server> 'python3 /data/pg-archive/migrate.py'

# 3. Seed ingest_state with current Mac file mtimes (so build doesn't re-scan)
~/claude-archive/pgsearch/.venv/bin/python <<'PYEOF'
import os, pathlib, psycopg2.extras, psycopg2
root = pathlib.Path.home() / ".claude/projects"
rows = [(str(j), j.stat().st_mtime, 0)
        for d in root.iterdir() if d.is_dir()
        for j in d.glob("*.jsonl")]
conn = psycopg2.connect(host="<your.domain>", port=5432, user="archive",
                        password="<pw>", dbname="archive_main", sslmode="require")
psycopg2.extras.execute_values(
    conn.cursor(),
    "INSERT INTO ingest_state (file_path, mtime, lines) VALUES %s "
    "ON CONFLICT (file_path) DO UPDATE SET mtime = EXCLUDED.mtime", rows)
conn.commit()
PYEOF
```

### 5. Verify

```bash
# Daemon up
launchctl list | grep pgsearchd
tail -5 ~/claude-archive/pgsearchd.log
# Expect: "pgsearchd: pool warmed (4 conns) in NNms"

# End-to-end FTS
csearch "any keyword you've used before" | head -3

# End-to-end vec (paraphrase that wouldn't FTS-match)
vsearch "上次卡很久那個 bug 怎麼解的" | head -3

# Cron writing to PG
tail -f ~/claude-archive/build.log
# Wait 15 min, expect: "+N rows" lines if jsonl changed
```

## Performance numbers (real-world, 2026-05-14, Mac → Singapore arcana.boo, ~50ms RTT)

| Operation | Sqlite (local) | PG via daemon | PG direct (--no-daemon) |
|---|---|---|---|
| csearch (FTS / pg_fts) cold | <50ms | ~700ms | ~1100ms |
| csearch warm | <10ms | ~280ms | ~970ms |
| vsearch (vec + Ollama embed) cold | ~600ms | ~500ms (after pre-warm) | ~1100ms |
| vsearch warm | ~150ms | **~380-500ms** | ~970ms |
| pgsearch --hybrid warm | n/a | ~600-800ms | ~1500ms |
| build incremental (100 new rows) | ~1s | ~10s | ~10s |
| embed-missing (8 workers) | ~50/s | ~5/s | ~5/s |

Daemon JSON breakdown via `crs pgsearch --vec --json '...'`:

```
source=daemon   connect=  1ms  query= 380ms      ← unix socket → pre-warmed pool
source=direct   connect=613ms  query= 390ms      ← every call: fresh TLS handshake
```

Daemon path saves the ~700ms handshake per query; the remaining ~380ms is Ollama bge-m3 embed (~150ms) + PG HNSW search + network round-trip. Cold path costs you the warm-up (Ollama loads model into memory, HNSW pages in).

## Failure modes / rollback

| Symptom | Likely cause | Fix |
|---|---|---|
| `connection refused` on daemon socket | daemon not running | `launchctl load com.jrjohn.pgsearchd.plist` |
| `connection refused` on direct PG | cloud security list / FG egress dropped | check ingress rule + corporate egress for tcp/5432 |
| `TLS handshake error: certificate verify failed` | Let's Encrypt cert expired | renew + run deploy hook (sec 2 above) |
| `relation "msg" does not exist` | schema not created on new db | re-run sec 3 SQL |
| build cron stuck / no new rows | ingest_state mtime gate | inspect: `SELECT * FROM ingest_state ORDER BY mtime DESC LIMIT 5` |
| every query slow even via daemon | pool connection died, daemon not reconnecting fast enough | restart daemon; pool max_lifetime default 30min should self-heal |
| `error retrieving column 0: error deserializing column 0` | NULL `ts` returned to non-Option type | already fixed in current code; if seeing this, you have stale binary |

**Full rollback to sqlite**: `git checkout` an earlier `crs` source where main.rs uses rusqlite paths, `cargo build --release`, daemon stays down (it's PG-specific). Mac sqlite at `~/claude-archive/sessions.db` is read-only after migration — you'd need to re-enable launchd build to populate. Easier path: migrate forward (which is what `crs build` already does for PG).

## Security trade-offs you accepted by going PG

Things that **moved out** of trust boundary "Mac only":

- All credentials/secrets ever pasted into chat (now query-able remotely)
- All conversation content
- All tool_use Bash commands + tool_result outputs

Things mitigating that:

- TLS 1.3 with Let's Encrypt cert (encrypts in transit)
- IP whitelist at cloud level (prevents random scanner)
- 32-char password (prevents brute force)
- Source IP also gated at corporate egress (FortiGate or equivalent)

Things that **don't** mitigate (consider before storing real credentials):

- Compromise of cloud account / server SSH = full archive
- Side-channel: any other container on same docker host could connect
- Phishing of your home/office static IP via BGP hijack (rare but possible)

If you also run an LLM agent (e.g. ZeroClaw, Claude Code with shell access) **on the same server**, it has direct access to the archive — keep this in mind for prompt injection vectors.

## Files & paths reference

```
Server side:
  /data/pg-archive/                       compose root
  /data/pg-archive/docker-compose.yml
  /data/pg-archive/.env                   POSTGRES_PASSWORD
  /data/pg-archive/data/                  postgres data dir (volume mount)
  /data/pg-archive/data/server.{crt,key}  Let's Encrypt cert (copied here)

Client side:
  ~/claude-archive/crs/                   Rust source
  ~/claude-archive/crs/target/release/crs single binary
  ~/Library/LaunchAgents/com.jrjohn.pgsearchd.plist
  ~/Library/LaunchAgents/com.jrjohn.claude-archive.plist
  ~/Library/Caches/pgsearchd/pgsearchd.sock
  ~/claude-archive/build.log              cron output
  ~/claude-archive/pgsearchd.log          daemon output
```
