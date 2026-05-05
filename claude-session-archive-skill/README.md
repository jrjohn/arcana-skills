# claude-session-archive-skill

Cross-session full-text + semantic history of every Claude Code conversation, stored locally. Pair this with Memory for a complete recall stack:

- **Memory** = curated signal (identity / traps / invariants — small)
- **This archive** = verbatim log (every command + result, every chat — large, query on demand)

Backed by SQLite FTS5 (lexical) and optionally Ollama + sqlite-vec (semantic, **bge-m3** 1024-dim, multilingual SOTA). Millisecond queries. Updates every 15 minutes via launchd / Task Scheduler / cron.

Deployment is **Rust (`crs`) — single ~5 MB self-contained binary** that bundles SQLite + FTS5 + sqlite-vec. No Python venv anywhere. Prerequisite: a `cargo` toolchain (rustup) on the install machine — the binary is then portable.

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

### Preflight enforcement (since v1.9.0) — `archive-preflight.sh` hook

The installer registers a **`PreToolUse` hook** on `Bash` and `Read` that enforces the preflight rule mechanically. The hook lives at `~/.claude/hooks/archive-preflight.sh` (or `archive-preflight.ps1` on Windows). Behavior per session:

| First action of the session | Outcome |
|---|---|
| `vsearch ...` or `csearch ...` | ✅ allowed → sets sentinel `/tmp/claude-archive-preflight-<session_id>` (or `%TEMP%\` on Windows) |
| `sqlite3 ~/claude-archive/sessions.db ...` | ❌ denied with reason — must run `vsearch`/`csearch` first |
| `grep / cat / head / tail / sed / awk` on `~/.claude/projects/*/memory/*.md` | ❌ denied — memory file is a stale index, not source of truth |
| `Read` tool on `~/.claude/projects/*/memory/*.md` | ❌ denied (same reason). `MEMORY.md` itself is exempted (auto-loaded by system). |
| Anything else | ✅ allowed silently |

Once `vsearch`/`csearch` runs once and sets the sentinel, subsequent `sqlite3` queries and memory grepping/reading are unblocked for the rest of the session.

**Why block memory grep too?** Memory files are hand-curated indexes — incomplete by design (only what someone bothered to write down). For "who is in dept X?", "what's .136 used for?", "where's password Y?" the canonical source is the archive (full conversation transcripts). Forcing `vsearch`/`csearch` first prevents the antipattern of grepping memory and silently missing 2/3 of the data that's actually in the archive.

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
./install.sh
# Optional semantic search:
./install-semantic.sh           # native Ollama
./install-semantic-docker.sh    # Docker variant
```

`install.sh` does: cargo build crs → mkdirs → copy sqliterc / gen-recent-context.sh → symlink `~/bin/crs` → write launchd plist (macOS) or crontab entry (Linux) pointing to `crs build` → register SessionStart hook (`crs gen-recent`) → install + register PreToolUse `archive-preflight.sh` hook (Bash + Read) in `~/.claude/settings.json` → first ingest.

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

## Trade-offs (pros / cons)

Honest evaluation as of 2026-05-04 (v1.7.3). Use this to decide whether the operational cost matches your recall needs.

### Pros

1. **Zero-maintenance background ingest.** launchd / Task Scheduler / cron every 15 min — no user friction once installed.
2. **Single Rust binary (~5 MB)** — bundles SQLite + FTS5 + sqlite-vec. No Python venv, no `pip install`. `cargo build` once on each new machine and ship the binary.
3. **Cross-platform parity.** macOS / Linux / Windows each have base + native-Ollama + Docker-Ollama installers.
4. **Three-tier graceful degradation.** `csearch` (always works, FTS lexical) → `vsearch` (semantic, optional) → `auto_recent.md` (Memory autoload). Each tier independently useful.
5. **Newest-first embed ordering.** Today's conversations become vsearchable in minutes, not hours, even during long initial backfills.
6. **Cross-language matching.** `bge-m3` (1024-dim multilingual SOTA) — "防火牆規則調整" matches "firewall policy edit" without a thesaurus.
7. **Idempotent installer.** Re-running rebuilds + re-wires hooks safely; no "uninstall first" dance.
8. **Memory ↔ DB separation is enforced by design.** Memory holds curated signal (small, high-density); DB holds verbatim log (large, queried on demand). Documented + reflected in `auto_recent.md` generation logic.

### Cons

1. **🔥 No health check / dashboard / alert.** A latent bug let `embed-missing` silently skip every new row for 6 days on at least one machine (the `pending = total - done` arithmetic broke once `msg_vec` accumulated stale rowids — fixed in v1.7.1/v1.7.2). FTS stayed current but vsearch returned only 4/28-and-older results. Detection took manual user-side curiosity. **No `crs doctor` subcommand exists yet.**
2. **Privacy / encryption.** DB captures every tool output verbatim — passwords, API tokens, IPs, MACs. Protection is `chmod 600` only; no encryption at rest. Loss / theft of the disk is a credential-disclosure event.
3. **Monotonic disk growth.** "Never delete old rows" is a stated invariant. 100k rows ≈ 731 MB. No retention policy, even opt-in. Move to external storage when tight.
4. **Embedding lag.** `vsearch` needs an ingest tick (≤ 15 min) to include the *current* session. `csearch` (FTS) is updated synchronously and has no lag. Documented in v1.7.3.
5. **`msg_vec` accumulates stale rowids.** When `msg.rowid` is reused after a re-ingest, the old vector lingers. Currently v1.7.2 papers over collisions with `INSERT OR REPLACE`, but **no `crs prune-vec` subcommand exists** to clean the stale tail. On one machine: `max(msg.rowid) = 513116` vs `count(msg) = 112304` → ~400k rowid gap, of which ~5k vec rows are orphans.
6. **Ollama is a single point of failure for vsearch / auto_recent.** Daemon down → semantic stack stalls. No alert path. (FTS keeps working.)
7. **No cross-machine transfer story.** No `crs export` / `crs import` / `crs sync`. Switching machines = re-ingest from scratch. Deliberate, but undocumented as a constraint.
8. **First-time backfill is long and silent.** 100k rows × ~9-12 emb/sec ≈ 2-3 hr on Apple Silicon (Metal); ~3-5× slower in Docker. No progress notification surfaces — user sees `backfill.log` only if they look.
9. **Errors fail silently.** Ingest / backfill failures land in log files but don't surface to the user. The 6-day vsearch outage in (1) is a direct consequence.

## Install hardening — proposed roadmap

Concrete improvements identified during the 2026-05-04 audit. Not yet implemented; ordered by ROI.

| # | Item | Impact | Effort |
|---|---|---|---|
| **1** | **`crs doctor` subcommand** — single command checks: cargo / sqlite3 / jq present, DB perms, launchd / Task / cron registered + last-run-success, SessionStart hook present, Ollama reachable, `bge-m3` pulled, `msg` vs `msg_vec` ratio, stale rowid count, embed backlog size. Catches the silent-failure class that bit us 2026-05-04. | High | Medium |
| **2** | **`crs prune-vec` subcommand** — `DELETE FROM msg_vec WHERE rowid NOT IN (SELECT rowid FROM msg)`. Run periodically or on demand. Prevents stale buildup; complements v1.7.2's `INSERT OR REPLACE`. | High | Small |
| **3** | **Prerequisite checks fail early in installers.** macOS/Linux: probe `jq`. Windows: probe `sqlite3.exe`. If missing, print exact install command and exit before half-running. | High (UX) | Small |
| **4** | **Unfreeze `OLLAMA_VER=v0.21.2`** in `install-semantic.sh`. Either fetch latest tag from GitHub Releases API or accept `OLLAMA_VER=…` env override (default = latest). | Medium | Small |
| **5** | **`uninstall.sh` / `uninstall.ps1`** — tear down launchd / Task / hook / symlink. Currently users with cold feet have to reverse-engineer the install steps. | Medium | Medium |
| **6** | **README operations section** — "How to verify the archive is healthy" with `crs doctor` + manual SQL probes. Surfaces this whole doc as a runbook, not just a feature list. | Medium (transparency) | Small |
| **7** | **Shell-rc detection in `install.sh`** — `$SHELL` env var isn't reliable across login styles; switch to inspecting which rc files exist + are non-empty, and add an explicit `source $RC` hint at the end. | Low | Small |
| **8** | **Linux systemd-timer alternative** to cron (parity with launchd). Detect at install time, prefer systemd if `systemctl --user` works, fall back to cron. | Low | Medium |
| **9** | **Windows path-with-spaces hardening** in `install.ps1` — explicit `"..."` quoting around `$Archive`, `$Bin`, `$BinDir`. Some users have `Documents and Settings`-era profile names that bite later. | Low | Small |
| **10** | **Docker semantic variant healthcheck wait.** Currently the install kicks off backfill before the container's `:11434` is necessarily ready; add a poll loop with timeout. | Low | Small |

### Suggested first batch (v1.8.0 candidate)

Items **1, 2, 3, 6** together close the operational visibility gap that produced the 2026-05-04 silent-failure incident:

- `crs doctor` (#1) — proactive catch.
- `crs prune-vec` (#2) — root-cause cleanup tool.
- Installer prereq checks (#3) — fail-early UX.
- README ops section (#6) — make all the above discoverable.

Estimated 1-2 hours total for someone with the codebase loaded. Other items can ship piecemeal in later patch releases.

## What's new

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
    └── ollama.plist.template         # macOS optional: Ollama auto-start
```

## Privacy

The DB captures **every tool output verbatim** — including passwords, tokens, API keys, IPs, MACs. Treat it like an SSH key:

- Local only (no rsync, iCloud, Dropbox)
- `chmod 600 ~/claude-archive/sessions.db`
- Wipe on Mac handover

## License / origin

Originally built 2026-04-24 for John Chang's internal IT workflow. Packaged as a generalized skill 2026-04-27. Free to use and modify.
