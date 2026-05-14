# claude-session-archive-skill

Cross-session full-text + semantic history of every Claude Code conversation, stored locally. Pair this with Memory for a complete recall stack:

- **Memory** = curated signal (identity / traps / invariants — small)
- **This archive** = verbatim log (every command + result, every chat — large, query on demand)

Backed by SQLite FTS5 (lexical) and optionally Ollama + sqlite-vec (semantic, **bge-m3** 1024-dim, multilingual SOTA). Single-machine mode: csearch ~6ms / vsearch ~300ms (embed-bound). Updates every 15 minutes via launchd / Task Scheduler / cron.

Deployment is **Rust (`crs`) — single ~5 MB self-contained binary** that bundles SQLite + FTS5 + sqlite-vec. No Python venv anywhere. Prerequisite: a `cargo` toolchain (rustup) on the install machine — the binary is then portable.

**Optional remote PG backend** (since v1.13): `cargo build --release --features pg-backend` (or `install.sh --with-pg`) re-routes csearch / vsearch / vsearch-since / build / embed-missing through a remote PostgreSQL 17 + pgvector instance. Adds `pgsearch` / `pgsearchd` subcommands; daemon holds an r2d2 connection pool over a unix socket so each query skips the ~700ms TLS handshake. Use this when you want the same archive across multiple machines. Performance trade-off: csearch ~315ms / vsearch ~1.1s end-to-end (WAN RTT-bound, not algorithm-bound — pure server query is ~6ms / ~200ms after v1.13.3's HNSW plan fix). Default sqlite build remains single-machine and 3-10× faster locally. See `references/pg-backend.md` for full setup.

## What it gives you

### `csearch` — FTS5 lexical (always available)
```bash
csearch ZyXEL                                 # cross-project keyword
csearch '"auto-power-down"' network           # phrase, project-filtered
csearch 'Sophos AND SEDService' network       # boolean
csearch 'somnic*'                             # prefix
```

### `vsearch` — semantic (optional Step 2)
```bash
vsearch '上次廣播 deny log 怎麼解的'           # concept query, no exact keyword
vsearch '防火牆規則調整' network              # also matches "firewall policy"
vsearch 'wireless AP keeps dropping' network  # vague description still works
```

Inside Claude:
> User: "上週那個 FortiGate shaper 怎麼設的？"
> Claude: *(silently runs `vsearch '上週 FortiGate shaper 設定' network`, reads the actual session, reports back)*

### Preflight order — vsearch first

**Claude defaults to `vsearch` and only falls back to `csearch` for explicit literals.** Reasons:

- vsearch tolerates fuzzy / cross-language phrasing — most user recall queries don't quote the exact original keyword
- `bge-m3` matches Chinese ↔ English concepts (e.g. `防火牆規則調整` → `firewall policy edit`) without a thesaurus
- A miss on csearch produces zero hits silently; a miss on vsearch still surfaces nearby semantic neighbours, which is more useful when the user is fishing

Skip vsearch and go straight to csearch only when the query is a precise literal — IP / hostname / file path / FTS5 boolean syntax / known key name. Pin this rule in `~/.claude/CLAUDE.md` (see snippet in `SKILL.md`).

### Preflight enforcement (since v1.9.0, hardened in v1.11.0) — `archive-preflight.sh` hook

The installer registers a **`PreToolUse` hook** on `Bash` and `Read` that enforces the preflight rule mechanically. The hook lives at `~/.claude/hooks/archive-preflight.sh` (or `archive-preflight.ps1` on Windows). Two tiers of rule:

**Tier A — hard deny (sentinel irrelevant; since v1.11):**

| Action | Outcome |
|---|---|
| `sqlite3 ... sessions.db` with `LIKE` / `MATCH` / `msg_fts` / `GLOB` | ❌ **always denied** — use `csearch` (FTS5) instead. csearch returns ts + project + role + ~258 chars per hit, covers credential / history / context lookups. |

**Tier B — sentinel-gated (any `vsearch`/`csearch` in last 30 min unlocks):**

| First action of the session | Outcome |
|---|---|
| `vsearch ...` or `csearch ...` | ✅ allowed → creates/refreshes sentinel `/tmp/claude-archive-preflight-<session_id>` (TTL 30 min) |
| `sqlite3 ... sessions.db` metadata (COUNT / PRAGMA / .schema / msg_vec) | ❌ denied — preflight discipline required even for maintenance |
| `grep / cat / head / tail / sed / awk` on `~/.claude/projects/*/memory/*.md` | ❌ denied — memory file is a stale index, not source of truth |
| `Read` tool on `~/.claude/projects/*/memory/*.md` | ❌ denied (same reason). `MEMORY.md` itself is exempted (auto-loaded by system). |
| `ssh ... grep|tail|cat ... /var/log/...` or local log grep | ❌ denied — investigative log digs duplicate prior session work |
| `git log --grep / -S` | ❌ denied — same logic |
| Anything else | ✅ allowed silently |

Once `vsearch`/`csearch` runs and sets the sentinel, Tier-B patterns unblock for 30 minutes. Every subsequent `vsearch`/`csearch` refreshes the TTL. After idle / compact gap (no archive query for >30 min), sentinel auto-expires and re-vsearch is required.

**Why hard-ban sqlite3 SEARCH (Tier A)?** csearch (FTS5) is strictly better for content lookup: faster than `LIKE`, supports phrase/boolean syntax, returns enough chars per hit to answer 99% of credential/history questions. Forcing csearch keeps archive-access discipline post-compact, where prose rules survive but procedural muscle memory doesn't. If csearch's defaults aren't enough for your case, extend its CLI (`scripts/crs/src/main.rs`) — don't bypass the hook.

**Why block memory grep too?** Memory files are hand-curated indexes — incomplete by design (only what someone bothered to write down). For "who is in dept X?", "what's .136 used for?", "where's password Y?" the canonical source is the archive (full conversation transcripts). Forcing `vsearch`/`csearch` first prevents the antipattern of grepping memory and silently missing 2/3 of the data that's actually in the archive.

**Why TTL (since v1.11)?** Post-compact, the model loses procedural memory of having run vsearch, but `session_id` (and thus the sentinel) persists. Without TTL, hooks would silently allow sqlite3 forever based on a vsearch from hours ago. 30-min TTL forces re-vsearch after any meaningful gap; `auto-vsearch-on-prompt.sh` refreshes the sentinel on archive-intent prompts so active conversations rarely hit it.

The hook is registered idempotently — re-running `install.sh` is safe.

### `auto_recent.md` — Memory bridge (since v1.4.0)

Every session start, a hook regenerates `<project>/memory/auto_recent.md` with the last-48h messages most semantically related to the project's open `pending` items (KNN over `msg_vec`, cosine ≤ 0.65, top 6 hits). Claude sees it automatically — no `csearch` needed for "what was I doing yesterday?"

A skip-guard avoids regenerating when nothing changed (`pending_mtime ≤ auto_recent_mtime` AND `latest_msg_ts ≤ auto_recent_mtime`), so idle projects don't burn Ollama on every cron tick.

## Quick install

One installer per platform. Builds the Rust `crs` binary, wires up the 15-min ingest schedule, registers the SessionStart hook, runs the first ingest. Semantic search (Ollama + bge-m3) is a separate optional step.

Prerequisite (all platforms): **Rust toolchain** — `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`.

### macOS / Linux

```bash
cd scripts
./install.sh                         # default: sqlite backend
./install.sh --with-pg               # OPTIONAL: enable pg-backend feature + install pgsearchd plist
# Optional semantic search (sqlite mode):
./install-semantic.sh                # native Ollama
./install-semantic-docker.sh         # Docker variant
```

`install.sh` does: cargo build crs (`--features pg-backend` if `--with-pg`) → mkdirs → copy sqliterc / gen-recent-context.sh → symlink `~/bin/crs` → write launchd plist (macOS) or crontab entry (Linux) pointing to `crs build` → on macOS with `--with-pg`, also write `~/Library/LaunchAgents/com.<USER>.pgsearchd.plist` (KeepAlive r2d2 daemon) → register SessionStart hook (`crs gen-recent`) → install + register PreToolUse `archive-preflight.sh` hook (Bash + Read) in `~/.claude/settings.json` → first ingest (skipped if `--with-pg` and `CRS_PG_PASSWORD` not yet set in env).

### Windows (PowerShell)

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned   # one-time

cd scripts
.\install.ps1
# Optional semantic search:
.\install-semantic.ps1          # OllamaSetup.exe
.\install-semantic-docker.ps1   # Docker Desktop variant
```

`install.ps1` does: cargo build crs.exe → mkdirs → copy sqliterc / csearch.ps1 / vsearch.ps1 / gen-recent-context.ps1 → register Scheduled Task `ClaudeArchiveIngest` (15 min, runs `crs.exe build`) → register SessionStart hook (`crs.exe gen-recent`) → install + register PreToolUse `archive-preflight.ps1` hook (Bash + Read) in `%USERPROFILE%\.claude\settings.json` → first ingest.

### Then (all platforms)

Paste the snippet from `SKILL.md` into `~/.claude/CLAUDE.md` (or `%USERPROFILE%\.claude\CLAUDE.md` on Windows) so future Claude sessions know to query the DB.

For step-by-step details and verification: `references/installation-guide.md`.

## Optional: semantic search (`vsearch`)

Adds concept / cross-language / synonym matching on top of `csearch`. Downloads Ollama + `bge-m3` (~1.3 GB) and runs a parallel backfill (8 workers, 4-5× faster than serial; ~1 hr native / ~3-5 hr Docker for 100k rows on Apple Silicon). Newest rows embed first so fresh conversations are queryable immediately.

```bash
# macOS / Linux
./scripts/install-semantic.sh           # native Ollama
./scripts/install-semantic-docker.sh    # Docker variant
```

```powershell
# Windows
.\scripts\install-semantic.ps1          # native Ollama (downloads OllamaSetup.exe)
.\scripts\install-semantic-docker.ps1   # Docker Desktop variant
```

After install, `crs vsearch` (or `vsearch.ps1` on Windows) works against the populated `msg_vec` table. See `references/semantic-search.md` for trade-offs.

## Operations — verify it's healthy

After install (or whenever vsearch / auto_recent feels stale), run:

```bash
crs doctor
```

What it checks (each line is `✓ OK`, `⚠ warn`, or `✗ fail`):

- **tooling** — `cargo` (required to rebuild), `sqlite3` + `jq` (optional)
- **storage** — archive dir exists, DB file exists + size, perms (`0600` on Unix)
- **database** — `msg` row count, `msg_vec` row count, **embed backlog** (rows in `msg` not yet in `msg_vec`), **stale rowids** (rows in `msg_vec` whose `msg.rowid` no longer exists), latest `msg.ts`
- **schedule** — launchd plist loaded (macOS) / cron entry present (Linux) / Scheduled Task registered (Windows)
- **hooks** — SessionStart hook for `crs gen-recent` in `~/.claude/settings.json`
- **ollama** — daemon reachable at `localhost:11434`, `bge-m3` model pulled

Exit code: `0` clean / `1` warnings / `2` failures — usable in cron / CI.

If `doctor` reports stale rowids:

```bash
crs prune-vec --dry-run    # preview count
crs prune-vec              # actually drop them
```

This drops `msg_vec` rows whose `msg.rowid` no longer exists (left over from re-ingest cycles where `msg.rowid` was reused). Cosmetic — vsearch already works thanks to v1.7.2's `INSERT OR REPLACE` — but keeps DB lean and `msg`/`msg_vec` counts close.

If `doctor` reports an embed backlog:

```bash
crs embed-missing          # parallel backfill, newest-first
```

Pair the two for a full reset:

```bash
crs prune-vec && crs embed-missing && crs doctor
```

## Architecture scorecard (v1.13.3, 2026-05-14)

Honest read on where the design wins and where it doesn't. Personal-grade tool — graded against the bar of "daily driver for a single power user", not production multi-tenant infra.

| Dimension | Score | Why |
|---|---|---|
| Search correctness (recall) | **9 / 10** | `bge-m3` 1024-dim multilingual, GIN + HNSW indexes both index-hit (after v1.13.3 plan fix). Role-filter + content-dedup at SQL layer (v1.13.2) drops ~30% noise rows. False positives rare. |
| Latency — sqlite mode | **9 / 10** | csearch ~6 ms, vsearch ~300 ms (embed dominates; Mac M4 + Metal bge-m3 ~110 ms). No network, no TLS. |
| Latency — PG mode | **6 / 10** | csearch ~315 ms / vsearch ~1.1 s end-to-end. Pure server query ~6 ms / ~200 ms — the rest is WAN RTT Mac↔VPS. Floor is geographic, not algorithmic. |
| Ops complexity — sqlite | **9 / 10** | One binary + cron + Ollama. `install.sh && forget`. No moving parts. |
| Ops complexity — PG | **5 / 10** | Container + TLS cert + Let's Encrypt renewal hook + password rotation + pgsearchd daemon + monitoring. Real maintenance surface. |
| Cross-platform parity | **7 / 10** | macOS / Linux / Windows installers all exist. Windows preflight stuck at v1.10.0; auto-vsearch hook macOS-only; pgsearchd unix-socket-only (Windows PG falls back to per-query connect). |
| Cross-machine recall | **7 / 10** | PG mode solves it (every machine queries same archive); sqlite mode is strictly single-machine. No export / import / sync tool — you're either all-in on PG or you re-ingest per machine. |
| Discipline enforcement | **9 / 10** | 3-layer hook stack: preflight (`PreToolUse` Bash+Read), auto-vsearch (`UserPromptSubmit`), sentinel TTL 30 min. Survives `/compact` — prose memory loss doesn't bypass mechanical rules. |
| Failure visibility | **7 / 10** | `crs doctor` catches storage / embed lag / hook registration / Ollama health. Doesn't catch: duplicate hook registration (just hit 2026-05-14), pgsearchd daemon crashed-then-respawning-loop, embedding-cache miss patterns. |
| Security at rest | **4 / 10** | `chmod 600` only. Full credentials / tokens / private chat captured verbatim. Disk theft = full exposure. No encryption, no key rotation, no redaction layer. |
| Discoverability (docs) | **6 / 10** | README + SKILL.md combined ~800 lines. Runbook is complete but heavy to skim; new readers struggle to find "the 30-second pitch" amid the changelog. |
| **Overall (personal-grade)** | **~7.5 / 10** | Solid daily driver. Not production-grade — no encryption, no backup automation, no alerting. The single-user trust model is load-bearing. |

## Trade-offs (pros / cons, v1.13.3)

Honest evaluation as of 2026-05-14. Use this to decide whether the operational cost matches your recall needs.

### Pros

1. **Zero-maintenance background ingest.** launchd / Task Scheduler / cron every 15 min — no user friction once installed.
2. **Single Rust binary (~5 MB)** — bundles SQLite + FTS5 + sqlite-vec. No Python venv, no `pip install`. `cargo build` once on each new machine, then portable.
3. **Two interchangeable backends, one source.** Cargo feature flag (`--features pg-backend`) toggles sqlite (default, fast local) vs PostgreSQL+pgvector (cross-machine). No code fork, no second binary.
4. **Three-layer discipline enforcement** that survives `/compact`: preflight hook (denies raw sqlite3 SEARCH + memory grep), auto-vsearch hook (proactive injection), sentinel TTL (forces re-vsearch after idle gap). Codified in hooks, not just prose.
5. **Newest-first embed ordering.** Today's conversations become vsearchable in minutes, not hours, during long backfills.
6. **Cross-language matching.** `bge-m3` (1024-dim multilingual SOTA) — `防火牆規則調整` matches `firewall policy edit` without a thesaurus.
7. **Idempotent installer.** Re-running rebuilds + re-wires hooks safely; no "uninstall first" dance.
8. **PG mode has a persistent daemon** (`pgsearchd`, r2d2 over unix socket) — every query skips the ~700 ms TLS handshake. Saves Mac↔VPS handshake on every csearch / vsearch.
9. **`crs doctor` catches the common silent failures** (embed lag, stale rowids, missing schedule, Ollama down, dead pgsearchd socket). Exit code 0/1/2 for cron-friendly CI.
10. **SQL-level dedup + role filter** (v1.13.2 / v1.13.3) cuts ~30 % of noise rows from auto-vsearch hook output. HNSW plan now actually hit, not Seq Scan.

### Cons

1. **PG-mode latency floor is geographic.** vsearch e2e ~1.1 s is dominated by WAN RTT Mac↔VPS, not algorithm. Sub-second only achievable by deploying pgsearchd on the same LAN as PG, or running sqlite locally.
2. **No encryption at rest.** DB captures every tool output verbatim — passwords, API tokens, IPs, MACs, private conversation. Protection is `chmod 600` only. Loss / theft of the disk is a credential-disclosure event.
3. **Monotonic disk growth.** Stated invariant: never delete old rows. 100 k rows ≈ 731 MB. No retention policy, even opt-in.
4. **Embedding lag.** `vsearch` needs an ingest tick (≤ 15 min) to include the *current* session's messages. `csearch` (FTS) is updated synchronously.
5. **Ollama is a single point of failure** for vsearch / auto_recent / auto-vsearch hook. Daemon down → semantic stack stalls. No alert path. (FTS / csearch keep working.)
6. **No backup automation.** Sqlite mode: `cp sessions.db` is the entire "backup tool". PG mode: `pg_dump` cron is not part of the installer — you have to wire it manually.
7. **Auto-vsearch hook regex is too broad.** Trigger set includes generic interrogatives (`怎麼`, `為什麼`, `請問`, `可以嗎`, `能不能`) → ~80 % of prompts fire vsearch. Cheap (~1.1 s) but not free. Plan to tighten.
8. **Windows is a second-class citizen.** Preflight hook (`archive-preflight.ps1`) stuck at v1.10.0 behavior (missing v1.11 hard-deny of `sqlite3 LIKE`, missing v1.13 PG-backend daemon support). Auto-vsearch hook is bash-only — no `.ps1` equivalent.
9. **`pgsearchd` resets HNSW `ef_search` per query** (via `SET hnsw.ef_search = N`). Plain `SET` (not `SET LOCAL`) means the value persists on the pooled connection — currently fine since every vsearch resets to the same value, but a future query type that needs a different `ef_search` would conflict.
10. **First-time backfill is long and quiet.** 100 k rows × ~9-12 emb/sec ≈ 2-3 hr on Apple Silicon (Metal); 3-5× slower in Docker. No progress notification surfaces — user sees `backfill.log` only if they look.
11. **No cross-machine sync for sqlite mode.** No `crs export` / `import` / `sync`. Switching machines = re-ingest from scratch, or migrate to PG.
12. **Trigger regex catches the hook duplicate-registration risk.** Same hook can be registered twice in `settings.json` (one with `~/...` and one with `/Users/.../`); `crs doctor` doesn't currently flag this. Hit 2026-05-14 — manual fix.

## Remaining roadmap

Most of the 2026-05-04 v1.7.3 audit roadmap shipped in v1.8.0–v1.13.0. What's still open:

| # | Item | Impact | Effort |
|---|---|---|---|
| 1 | **Encrypt-at-rest option** — `sqlite-cipher` or PG TDE. Make this opt-in via `install.sh --encrypted`; key in macOS Keychain / Windows DPAPI / Linux secret-service. | High (security) | Large |
| 2 | **`uninstall.sh` / `uninstall.ps1`** — tear down launchd / Task / hook / symlink / pgsearchd plist. | Medium | Medium |
| 3 | **`pg_dump` cron in installer** (PG mode) — daily backup to local file or S3, with rotation. | Medium | Small |
| 4 | **`crs doctor`: duplicate hook detection** — scan `settings.json` for repeated hook commands. | Medium (UX) | Small |
| 5 | **Tighten `ARCHIVE_TRIGGER` regex** in `auto-vsearch-on-prompt.sh` — strip generic interrogatives, keep only history-intent keywords. | Medium (cost) | Small |
| 6 | **Windows preflight + auto-vsearch parity** — port v1.11 hard-deny rules and `.ps1` UserPromptSubmit hook. | Medium | Medium |
| 7 | **Optional: `pgsearchd` deployment on VPS** + thin RPC client on Mac. Cuts vsearch e2e ~1.1 s → ~400 ms (saves WAN RTT). | Medium | Medium |
| 8 | **Linux systemd-timer alternative** to cron (parity with launchd). | Low | Medium |
| 9 | **Docker semantic variant healthcheck wait** — poll `:11434` before kicking off backfill. | Low | Small |
| 10 | **Unfreeze `OLLAMA_VER`** in `install-semantic.sh` — fetch latest release tag at install time. | Low | Small |

## What's new

### v1.13.3 — pg_vec HNSW plan fix (vsearch 9–13 s → 1.1 s)

v1.13.2 added `role IN ('user','assistant')` as an inline `WHERE` filter on `msg`. The filter matches ~71 % of rows, so the planner judged Seq Scan + sort cheaper than HNSW + filter and dropped index use entirely. `EXPLAIN ANALYZE` confirmed Seq Scan over 98 k rows + top-N heapsort = 6.275 s server-side.

Fix: `MATERIALIZED` HNSW-first CTE (same pattern as pg_fts in v1.13.1) — HNSW returns ~40 candidates, role-filter applies on the small set, then `DISTINCT ON (content) ORDER BY content, dist` for dedup. Also raises `hnsw.ef_search = max(over_fetch, 100)` so the index walk actually surfaces enough candidates (default 40 too small for over_fetch=100+). Server-side now 210 ms; end-to-end from Mac through TLS via pgsearchd daemon ~1.1 s (was 9–13 s).

### v1.13.2 — pg_fts / pg_vec role filter + content dedup

UserPromptSubmit auto-vsearch hook was wasting token slots on (a) `tool_use` / `tool_result` rows where role is not user/assistant, (b) duplicate content (same prompt or system event stored multiple times — user row + `queue-operation` row + `ai-title` row, all embedded identically).

Fix at SQL layer (benefits manual `vsearch` / `csearch` CLI too):

- **pg_vec**: `WHERE role IN ('user','assistant')` inside the HNSW pipeline + `ROW_NUMBER() OVER (PARTITION BY content)` dedup with over-fetch.
- **pg_fts**: same role filter inside the existing `MATERIALIZED` hits CTE + `DISTINCT ON (content) ORDER BY content, ts DESC` dedup.

vsearch top-8 now returns 8 distinct user prompts (previously 3-4 distinct due to TOOL_RESULT noise crowding out real hits). Note: v1.13.2 inadvertently killed HNSW index use; corrected in v1.13.3.

### v1.13.1 — pg_fts MATERIALIZED CTE — force GIN scan

`csearch` (pg_fts mode) was hitting 432 ms server-side because the planner picked a B-tree `msg_ts_idx` backward scan + per-row tsvector filter, ignoring the GIN index on `content_tsv`. Wrapping the filter+match in a `MATERIALIZED` CTE forces the planner to evaluate the GIN scan first, then sort the small hit set by `ts DESC`. Server-side dropped 432 ms → 6 ms (72×). End-to-end ~315 ms over WAN.

### v1.13.0 — PG backend behind Cargo feature flag + credential scrub + pgsearchd plist template

The 2026-05-14 PG migration (v1.12.0) shipped with `csearch / vsearch / vsearch-since / build / embed-missing` hard-coded to PG and `PG_HOST/USER/PASS/DB` as `const &str` literals in `src/main.rs`. That made the sqlite path unreachable from a binary built off this repo, and (worse) put bluesea credentials into anyone's clone. v1.13 fixes both:

- **Same source builds either backend** via Cargo feature. `cargo build --release` → sqlite-only (default). `cargo build --release --features pg-backend` → PG-routed (csearch / vsearch / vsearch-since / build / embed-missing dispatch through `pg_search_dispatch`; `pgsearch` + `pgsearchd` subcommands appear). `Pgsearchd` is additionally `#[cfg(unix)]` (Windows falls back to direct connect on every query). The default build doesn't even download the postgres / r2d2 / native-tls deps — gated by `optional = true` + `[features] pg-backend = ["dep:..."]`.
- **Credentials → env vars**: read at runtime from `CRS_PG_URL` (full libpq string) OR `CRS_PG_HOST/PORT/USER/PASSWORD/DB` (component-wise; PASSWORD required, others default to `localhost / 5432 / archive / archive_main`). `crs --features pg-backend` refuses to start without `CRS_PG_PASSWORD`, with a clear error pointing to `references/pg-backend.md`. **No password ever lives in source.**
- **`install.sh --with-pg`** (or `WITH_PG=1`): passes `--features pg-backend` to cargo and additionally writes `~/Library/LaunchAgents/com.<USER>.pgsearchd.plist` from the new `scripts/pgsearchd.plist.template` (`KeepAlive` + `EnvironmentVariables` block for CRS_PG_*). Skips first-ingest if `CRS_PG_PASSWORD` not set. Linux: prints a systemd-user-unit guidance message.
- **`crs doctor`** gains a `[pg-backend]` block when feature enabled — checks env vars, runs `SELECT 1`, reports `msg` row count, looks for the `pgsearchd.sock`. Cleaner failure mode than mid-query crash.
- **`gen-recent-context`** skip-guard: in pg-backend mode queries PG for `MAX(ts)` (sqlite is empty in PG mode). Falls back to pending-mtime-only guard if PG unreachable — avoids blocking SessionStart on a network blip.
- **`references/pg-backend.md`** rewritten — section 1 ("Build crs for PG mode") now documents env vars + feature flag instead of "edit constants". Performance table refreshed with 2026-05-14 measurements (csearch warm 280ms / vsearch warm 380ms via daemon; +700ms TLS handshake without daemon). Daemon-vs-direct breakdown via `--json` output of `pgsearch`.

**Migrating an existing PG install**: re-run `install.sh --with-pg`, edit the new `~/Library/LaunchAgents/com.<USER>.pgsearchd.plist` to set `CRS_PG_PASSWORD`, then `launchctl unload && load`. Existing socket / pool / launchd label / data unchanged. Old hardcoded source can be discarded.

### v1.11.0 — Preflight hardening: forbid sqlite3 SEARCH + 30-min sentinel TTL

Two independent fixes prompted by a 2026-05-11 post-compact incident where Claude went straight to `sqlite3 ... LIKE '%X%'` for a credential lookup instead of csearch:

- **Hard-deny `sqlite3 SEARCH` on `sessions.db`.** Patterns `LIKE`, `MATCH`, `msg_fts`, `GLOB` are now blocked **regardless of sentinel state**. csearch is the only supported interface for content search. Motivation: CLAUDE.md prose said "vsearch first" but its credential-lookup section literally used raw `sqlite3 LIKE` as the example — that pattern survived compact as the model's procedural muscle memory. Moving the rule from prose into the hook + rewriting all credential examples to use csearch closes the gap. csearch returns ts + project + role + ~258 chars per hit (covers 99% of credential/history/context lookups); if your case needs more, extend the csearch CLI rather than bypass the hook. Metadata queries (`COUNT`, `PRAGMA`, `.schema`, `msg_vec` maintenance) remain allowed for backfill checks.
- **30-minute sentinel TTL.** The sentinel file (`/tmp/claude-archive-preflight-<sid>`) now expires 30 minutes after creation. `sentinel_valid()` checks mtime, auto-removes stale files. Motivation: post-compact, the model loses procedural memory of having run vsearch but `session_id` (and thus sentinel) persists — without TTL, the hook would allow Tier-B operations forever based on a vsearch from hours ago. `auto-vsearch-on-prompt.sh` refreshes the sentinel on every archive-intent prompt, so active conversations don't notice the TTL; it only kicks in after compact / idle gaps.
- **CLAUDE.md credential section rewritten** to follow `vsearch → csearch` 2-tier hierarchy, with all `sqlite3 LIKE` examples removed and a "禁用 raw sqlite3 搜尋" callout listing the hard-denied patterns.

Windows port (`archive-preflight.ps1`) not updated this release — Windows installs continue at v1.10.0 preflight behavior.

`install.sh` is unchanged structurally — re-running it idempotently replaces the preflight hook with the v1.11 version.

### v1.9.0 — Preflight enforcement hook (memory grep + sqlite3 gating)

Adds a `PreToolUse` hook (`archive-preflight.sh` / `archive-preflight.ps1`) that **mechanically enforces the vsearch-first preflight** documented since v1.6.2. Previously the rule was prose-only (in CLAUDE.md and SKILL.md), which Claude could and did skip. Now:

- **Hook is registered for both `Bash` and `Read` matchers** in `~/.claude/settings.json`.
- **First action of the session must be `vsearch` or `csearch`** — otherwise `sqlite3 ~/claude-archive/sessions.db ...` is denied with a hint.
- **NEW: memory file grep / Read is also gated.** `~/.claude/projects/*/memory/*.md` is treated as a stale, hand-curated index; for "who is in dept X?" / "what's .136?" / "where's password Y?" the canonical source is the archive (full transcripts), not memory. `MEMORY.md` itself is exempted (it's auto-loaded by the system anyway).
- Sentinel file (`/tmp/claude-archive-preflight-<session_id>` on Unix, `%TEMP%\` on Windows) unblocks the rest of the session after one `vsearch`/`csearch` run.

Motivation: an audit on 2026-05-05 found Claude grepping memory for a 6-person department roster, hitting only 2 of 6 because memory only mentioned the 2 employees that had previously triggered an incident. A `csearch` would have hit the full 4/24 audit transcript with all 6. Codifying the rule in a hook prevents the antipattern at runtime, not just in docs.

`install.sh` / `install.ps1` install the hook idempotently. Both auto-add the matcher entries via `jq` (Linux/Mac) or `ConvertFrom-Json` (Windows). Re-running the installer is safe.

See README "Preflight enforcement (since v1.9.0)" section for the full behavior table.

### v1.8.0 — `crs doctor` + `crs prune-vec` + installer prereq surfacing

First batch from the 2026-05-04 audit. Closes the operational visibility gap that produced the silent vsearch outage:

- **`crs doctor`** — single-command health check across tooling, storage, DB consistency, schedule, hooks, and Ollama. Exit code 0 / 1 / 2 = clean / warn / fail (cron-friendly).
- **`crs prune-vec`** — drops orphaned `msg_vec` rowids left over after re-ingest. Supports `--dry-run`. Pairs with v1.7.2's `INSERT OR REPLACE` (defence in depth: collisions are tolerated *and* cleanable).
- **Installer prereq surfacing.** `install.sh` now lists `jq` / `sqlite3` status with exact install commands per OS before mid-run discovery. `install.ps1` downgrades `sqlite3.exe` from a fatal abort to a warning (since `crs.exe` already bundles SQLite — `sqlite3.exe` is only needed for raw `sqlite3 sessions.db` queries). `install-semantic.ps1` now skips its row-count probe gracefully when `sqlite3.exe` is absent rather than erroring.
- **README ops section** documents `crs doctor` / `crs prune-vec` workflows so they're discoverable without reading the changelog.

Implements items 1, 2, 3, 6 from the install-hardening roadmap. Items 4, 5, 7-10 remain candidates for later patch releases.

### v1.7.0 — Rust-only

Dropped Python entirely. `crs` (Rust) is now the **base**, no longer optional acceleration. One installer per platform: `install.sh` (macOS/Linux) / `install.ps1` (Windows) builds cargo and wires up launchd / Scheduled Task / SessionStart hook in one step. Removed `build.py / embed.py / embed_parallel.py / vsearch.py / vsearch-since.py / csearch.py` and the bash `csearch / vsearch` wrappers. `install-semantic.*` no longer creates a Python venv — only installs Ollama + bge-m3 and triggers `crs embed-missing` for backfill. **Prerequisite changed**: now requires `cargo` (rustup) instead of `python3`. Migration on existing installs: re-run the new `install.sh` — it auto-rewires the launchd plist + SessionStart hook.

### v1.6.3 — `install-rust-accel.sh` auto-appends `~/bin` to PATH

Closes a gap with the main install. The macOS/Linux base install snippet in this README conditionally appends `export PATH="$HOME/bin:$PATH"` to `~/.zshrc` / `~/.bashrc` when `~/bin` is missing from `PATH`. The Rust accel installer was only **printing a note** ("note: add to ~/.zshrc: …") and leaving the user to act. If `~/bin` wasn't already on PATH at that point, the bare `crs` / `csearch` / `vsearch` commands silently failed in interactive shells (launchd kept working because it uses absolute paths). The Rust installer now matches the base install: detects shell (`zsh` → `~/.zshrc`, `bash` → `~/.bashrc`, else `~/.profile`), checks if `~/bin` is already referenced, and appends the export only when missing. Idempotent. Windows installers (`install.ps1` / `install-rust-accel.ps1`) were already correct via `[Environment]::SetEnvironmentVariable("Path", …, "User")`. No binary changes.

### v1.6.2 — `vsearch`-first preflight

Default Claude query order flipped: **`vsearch` first, `csearch` only as fallback for explicit literals.** Rationale: most past-session recall queries are paraphrased ("上次怎麼處理 X 的"), not verbatim — semantic match wins. `csearch` stays the right tool for IPs, hostnames, file paths, and FTS5 boolean syntax. README, `SKILL.md` trigger table, `references/semantic-search.md` decision flow, and the installation-guide verification line all updated to match. No behaviour change in the binaries — pure documentation / prompt-engineering update. Pair this with a `~/.claude/CLAUDE.md` snippet pinning the same rule.

### v1.6.1 — vec0 statically linked

`crs` now bundles `sqlite-vec` C source via the `sqlite-vec` Rust crate. **No more runtime `load_extension(vec0.dylib)`**, which previously needed the Python venv to be present even though Rust did the actual work. You can now `mv ~/claude-archive/.venv elsewhere` and `vsearch` still works. Binary 4.9 → 5.0 MB. (FTS5 was already statically linked since v1.6.0 via rusqlite's `bundled` feature with `SQLITE_ENABLE_FTS5`.)

### v1.6.0 — Rust acceleration (`crs`)

Single binary replaces every Python helper:

| Python | Rust subcommand |
|---|---|
| `build.py` | `crs build` |
| `embed_parallel.py` | `crs embed-missing` |
| `vsearch.py` | `crs vsearch` |
| `vsearch-since.py` | `crs vsearch-since` |
| `csearch.py` | `crs csearch` |
| `gen-recent-context.{sh,ps1}` | `crs gen-recent` |

Bench (Apple M4):

| Path | Python | Rust | Speedup |
|---|---|---|---|
| process startup | 80 ms | <5 ms | **>16×** |
| `csearch` (FTS5) | 20 ms | <5 ms | **>4×** |
| `gen-recent` SKIP path | 10 ms | <5 ms | ~3-5× |
| `build` steady-state no-op | 20-100 ms | <5 ms | 5-20× |
| `gen-recent` regen path | 340 ms | 260 ms | 1.3× (Ollama-bound) |
| `build` cold re-ingest 84 files | 6.13 s | 5.86 s | 1.05× (I/O-bound) |
| `embed-missing` backfill | n/a | n/a | ≈1× (Ollama-bound) |

The real value isn't raw speed — Ollama-bound paths are unmoved. It's **deployment**: drop the Python venv from the launchd plist, ship one ~5 MB binary, no `pip install`, no `requirements.txt`. Source ~720 LOC at `scripts/crs/`.

### v1.5.0 — Energy-aware `auto_recent.md`

- **vsearch-on-pending replaces three-section dump.** Old design wrote pending excerpt + 8 user prompts + 5 assistant replies (49 lines, often noisy). New design uses the project's pending list as a semantic query against last-48h `msg_vec` rows (KNN, cosine ≤ 0.65) and surfaces the top 6 hits actually related to open work. Pending itself is **not** duplicated — Claude reads `project_pending.md` from the MEMORY.md index when it needs the full text. ~Half the auto-loaded token budget vs. v1.4.0.
- **Skip guard.** `gen-recent-context.{sh,ps1}` exits early when neither the pending file nor the DB has changed since the last regen. Idle projects no longer trigger Ollama embed + KNN every 15 minutes. `FORCE_REGEN=1` overrides. Logs `[OK] / [SKIP] / [ERROR]` to `~/claude-archive/gen-recent-context.log`.
- **Newest-first embed ordering** (`ORDER BY rowid DESC`). During long initial backfills, today's conversations become queryable in minutes instead of waiting for the entire historical corpus.
- **`vsearch-since`** — time-bounded (`--hours`) + cosine-cutoff (`--max-distance`) + length filter (`--min-len` / `--max-len`). Standalone-callable; also used by `gen-recent-context`.
- **Windows parity.** `gen-recent-context.ps1` ports the bash version. `install.ps1` auto-registers the SessionStart hook (no more WSL-only TODO).

### v1.4.0 — Memory bridge

`gen-recent-context.{sh,ps1}` + SessionStart hook + `build.py` per-project refresh. Per-project `auto_recent.md` is auto-generated at every session start and refreshed every 15 min — so Claude always has fresh context loaded into Memory at session start, without explicit queries.

Full changelog in `SKILL.md`.

## What's in this skill

```
claude-session-archive-skill/
├── SKILL.md                          # Skill entry — read this first
├── README.md                         # this file
├── references/
│   ├── installation-guide.md         # step-by-step setup walkthrough
│   ├── fts5-syntax.md                # FTS5 query language reference
│   ├── tuning.md                     # SQLite performance + maintenance
│   ├── faq.md                        # common errors / questions
│   └── semantic-search.md            # OPTIONAL: Ollama + sqlite-vec for vsearch
└── scripts/
    │   # Rust source (the only runtime code)
    ├── crs/                          # ~720 LOC: build / embed-missing / vsearch / csearch / vsearch-since / gen-recent
    │
    │   # Installers — base (compiles crs + wires schedule + first ingest)
    ├── install.sh                    # macOS / Linux
    ├── install.ps1                   # Windows
    │
    │   # Installers — optional semantic stack (Ollama + bge-m3, no Python)
    ├── install-semantic.sh           # macOS / Linux: native Ollama
    ├── install-semantic-docker.sh    # macOS / Linux: Docker variant
    ├── install-semantic.ps1          # Windows: OllamaSetup.exe
    ├── install-semantic-docker.ps1   # Windows: Docker Desktop variant
    │
    │   # Hooks / wrappers / templates
    ├── gen-recent-context.sh         # SessionStart hook (bash) — calls crs vsearch-since
    ├── gen-recent-context.ps1        # SessionStart hook (PowerShell)
    ├── csearch.ps1                   # Windows PowerShell csearch wrapper (sqlite3.exe)
    ├── vsearch.ps1                   # Windows PowerShell vsearch wrapper (calls crs.exe)
    ├── sqliterc.template             # → ~/.sqliterc (SQLite tuning)
    ├── launchd.plist.template        # macOS: → ~/Library/LaunchAgents/com.USER.claude-archive.plist (runs crs build)
    ├── pgsearchd.plist.template      # macOS PG-backend optional: → ~/Library/LaunchAgents/com.USER.pgsearchd.plist (KeepAlive r2d2 daemon)
    └── ollama.plist.template         # macOS optional: Ollama auto-start
```

## Privacy

The DB captures **every tool output verbatim** — including passwords, tokens, API keys, IPs, MACs. Treat it like an SSH key:

- Local only (no rsync, iCloud, Dropbox)
- `chmod 600 ~/claude-archive/sessions.db`
- Wipe on Mac handover

## License / origin

Originally built 2026-04-24 for John Chang's internal IT workflow. Packaged as a generalized skill 2026-04-27. Free to use and modify.
