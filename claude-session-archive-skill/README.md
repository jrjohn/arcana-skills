# claude-session-archive-skill

Cross-session full-text + semantic history of every Claude Code conversation, stored locally. Pair this with Memory for a complete recall stack:

- **Memory** = curated signal (identity / traps / invariants — small)
- **This archive** = verbatim log (every command + result, every chat — large, query on demand)

Backed by SQLite FTS5 (lexical) and optionally Ollama + sqlite-vec (semantic, **bge-m3** 1024-dim, multilingual SOTA). Millisecond queries. Updates every 15 minutes via launchd / Task Scheduler / cron.

Default deployment is **Rust (`crs`) — single ~5 MB binary, no venv, no Python required at runtime.** Python scripts ship as a fallback for environments without a Rust toolchain.

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

### `auto_recent.md` — Memory bridge (since v1.4.0)

Every session start, a hook regenerates `<project>/memory/auto_recent.md` with the last-48h messages most semantically related to the project's open `pending` items (KNN over `msg_vec`, cosine ≤ 0.65, top 6 hits). Claude sees it automatically — no `csearch` needed for "what was I doing yesterday?"

A skip-guard avoids regenerating when nothing changed (`pending_mtime ≤ auto_recent_mtime` AND `latest_msg_ts ≤ auto_recent_mtime`), so idle projects don't burn Ollama on every cron tick.

## Quick install

Two-step pattern on every platform: **(1) base** sets up the DB + 15-min ingest, **(2) accelerator** replaces Python with the Rust `crs` binary. Step (2) is recommended but optional — the Python scripts work fine on their own.

### macOS

```bash
cd scripts

# 1. Base — DB + launchd + Python helpers
mkdir -p ~/claude-archive ~/bin
cp build.py ~/claude-archive/build.py     && chmod +x ~/claude-archive/build.py
cp csearch  ~/bin/csearch                 && chmod +x ~/bin/csearch
cp sqliterc.template ~/.sqliterc
echo $PATH | grep -q "$HOME/bin" || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
USER=$(whoami)
sed "s/<USERNAME>/$USER/g" launchd.plist.template > ~/Library/LaunchAgents/com.${USER}.claude-archive.plist
launchctl load ~/Library/LaunchAgents/com.${USER}.claude-archive.plist
python3 ~/claude-archive/build.py            # first ingest

# 2. Rust accelerator (recommended) — single binary, no venv at runtime
./install-rust-accel.sh                      # needs rustup; ~2-5 min first build
```

### Linux

```bash
cd scripts

# 1. Base — DB + cron + Python helpers
mkdir -p ~/claude-archive ~/bin
cp build.py ~/claude-archive/build.py     && chmod +x ~/claude-archive/build.py
cp csearch  ~/bin/csearch                 && chmod +x ~/bin/csearch
cp sqliterc.template ~/.sqliterc
echo $PATH | grep -q "$HOME/bin" || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
( crontab -l 2>/dev/null; echo "*/15 * * * * /usr/bin/python3 $HOME/claude-archive/build.py >/dev/null 2>&1" ) | crontab -
python3 ~/claude-archive/build.py            # first ingest

# 2. Rust accelerator (recommended)
./install-rust-accel.sh
```

> The Rust installer auto-rewires the launchd plist on macOS. On Linux it builds `crs` and symlinks `~/bin/crs`; you'll need to update your crontab to call `~/bin/crs build` instead of `python3 build.py` (one-line edit).

### Windows (PowerShell)

```powershell
# One-time: allow local script execution
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

cd scripts

# 1. Base — DB + Scheduled Task + csearch.ps1 + SessionStart hook auto-registered
.\install.ps1

# 2. Rust accelerator (recommended) — needs rustup
.\install-rust-accel.ps1
```

`install.ps1` does mkdirs → copy build.py / csearch.ps1 / sqliterc → register Scheduled Task `ClaudeArchiveIngest` (15 min) → first ingest → add `%USERPROFILE%\bin` to PATH → register SessionStart hook in `%USERPROFILE%\.claude\settings.json`.

`install-rust-accel.ps1` builds `crs.exe`, copies to `%USERPROFILE%\bin\`, and rewires the Scheduled Task + SessionStart hook to use the binary.

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

After install, `vsearch` is on PATH (or `vsearch.ps1` on Windows). The `crs vsearch` Rust subcommand also works against the same `msg_vec` table once embeddings exist. See `references/semantic-search.md` for trade-offs.

## What's new

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
    │   # Rust (default since v1.6) — single ~5 MB binary, no venv
    ├── crs/                          # Rust source (~720 LOC: build / embed / vsearch / csearch / gen-recent)
    ├── install-rust-accel.sh         # macOS / Linux installer (rustup + cargo build)
    ├── install-rust-accel.ps1        # Windows installer
    │
    │   # Python fallback / bootstrap
    ├── build.py                      # JSONL → SQLite ingest
    ├── csearch                       # CLI lexical search (bash)
    ├── csearch.py                    # core
    ├── csearch.ps1                   # PowerShell wrapper
    ├── embed.py                      # Ollama embedding helper (newest-first)
    ├── embed_parallel.py             # parallel backfill (8 workers, 4-5× faster)
    ├── vsearch                       # CLI semantic search (bash)
    ├── vsearch.py                    # core
    ├── vsearch.ps1                   # PowerShell wrapper
    ├── vsearch-since.py              # time-bounded semantic search
    ├── gen-recent-context.sh         # SessionStart hook (bash)
    ├── gen-recent-context.ps1        # SessionStart hook (PowerShell)
    │
    │   # Templates / installers
    ├── sqliterc.template             # → ~/.sqliterc (SQLite tuning)
    ├── launchd.plist.template        # macOS: → ~/Library/LaunchAgents/com.USER.claude-archive.plist
    ├── ollama.plist.template         # macOS optional: Ollama auto-start
    ├── install.ps1                   # Windows base installer
    ├── install-semantic.sh           # macOS / Linux: native Ollama + vsearch
    ├── install-semantic-docker.sh    # macOS / Linux: Docker variant
    ├── install-semantic.ps1          # Windows: native Ollama (OllamaSetup.exe)
    └── install-semantic-docker.ps1   # Windows: Docker Desktop variant
```

## Privacy

The DB captures **every tool output verbatim** — including passwords, tokens, API keys, IPs, MACs. Treat it like an SSH key:

- Local only (no rsync, iCloud, Dropbox)
- `chmod 600 ~/claude-archive/sessions.db`
- Wipe on Mac handover

## License / origin

Originally built 2026-04-24 for John Chang's internal IT workflow. Packaged as a generalized skill 2026-04-27. Free to use and modify.
