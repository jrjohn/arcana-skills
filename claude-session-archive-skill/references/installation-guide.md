# Installation Guide — Claude Session Archive

Detailed step-by-step setup. For the conceptual overview see `../SKILL.md`.

## Layered design

| Layer | Purpose | Maintained by |
|---|---|---|
| **JSONL** (`~/.claude/projects/*/*.jsonl`) | Raw verbatim per-session log | Claude Code (automatic) |
| **SQLite FTS5** (`~/claude-archive/sessions.db`) | Cross-session full-text + vector index | This skill (`crs build`, every 15 min via launchd / cron / Task Scheduler) |
| **Memory** (`~/.claude/projects/*/memory/`) | Curated signal: identity, traps, invariants | Claude (writes when learning something durable) |

## Architecture

```
~/.claude/projects/*/*.jsonl        (Claude Code writes automatically)
              │
              ▼ crs build (incremental, idempotent — Rust binary)
~/claude-archive/sessions.db        (SQLite + FTS5 + sqlite-vec, all bundled in crs)
              │
              ├── ~/bin/crs                       single binary: build / csearch / vsearch / vsearch-since / gen-recent / embed-missing
              ├── sqlite3 <db> "SELECT ..."       direct SQL
              ├── ~/.sqliterc                     cache/mmap/temp_store tuning
              └── ~/.claude/CLAUDE.md             instructions for future Claude
```

DB schema:
```sql
msg(session_id, project, seq, ts, role, tool_name, content)  PRIMARY KEY (session_id, seq)
msg_fts                  -- virtual FTS5 over content, tokenize=unicode61
msg_vec                  -- vec0 (cosine), 1024-dim bge-m3 embeddings (only after install-semantic.sh)
ingest_state(file_path, mtime, lines)
```

---

## Prerequisites

- **Rust toolchain (`cargo`)** — install via rustup:
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  ```
  Re-open shell so `cargo` is on PATH.
- **sqlite3** CLI (almost always pre-installed; `brew install sqlite` / `apt install sqlite3` if missing).
- **(Optional)** `jq` for automatic SessionStart hook registration in `install.sh`. Without it, the hook line is printed for manual paste.

No Python needed. No venv anywhere.

---

## Step 1 — Run the base installer

The installer compiles the `crs` Rust binary, writes the launchd plist (macOS) or crontab entry (Linux), copies sqliterc, registers the SessionStart hook, and runs the first ingest — all idempotent.

```bash
cd scripts
./install.sh
```

What it does:
1. Verify `cargo` present
2. `mkdir -p ~/claude-archive ~/bin`
3. Copy `crs/` source → `cargo build --release` (~2-5 min first time, cached afterward)
4. `~/bin/crs` symlink + ensure `~/bin` on PATH (auto-appends to `~/.zshrc` / `~/.bashrc` / `~/.profile`)
5. `~/.sqliterc` tuning
6. Copy `gen-recent-context.sh` to `~/claude-archive/`
7. Schedule the 15-min ingest:
   - **macOS**: writes `~/Library/LaunchAgents/com.<USER>.claude-archive.plist` calling `crs build`, runs `launchctl load`
   - **Linux**: adds `*/15 * * * * /usr/bin/flock -n /tmp/crs-build.lock ~/claude-archive/crs/target/release/crs build` to crontab. The `flock -n` prevents the next cron tick from stacking when a slow build (Ollama unhealthy, embed backlog) overruns 15 min — see cloud-deployment.md "Ollama Stopping cascade" gotcha for what happens without it.
8. Register `crs gen-recent` as a SessionStart hook in `~/.claude/settings.json` (skipped if already present; needs `jq`)
8b. Install `archive-preflight.sh` to `~/.claude/hooks/` and register it as a PreToolUse hook for both `Bash` and `Read` matchers (gates raw `sqlite3` against the archive DB and `grep`/`Read` on memory files until `vsearch`/`csearch` runs once per session — see README "Preflight enforcement" section)
9. First ingest (`crs build --no-embed`) — populates `msg` + `msg_fts`
10. Smoke test: prints `crs --help`

Expected output of step 9 (first ingest):
```
+XXXX  -Users-USER-Documents-projects-foo/abc123.jsonl
...
touched N files, +M rows
DB total: M rows / S sessions / P projects
```

## Step 2 — Verify

```bash
ls -la ~/claude-archive/sessions.db        # exists, > 1MB after first ingest
crs csearch claude                         # returns at least one row
launchctl list | grep claude-archive       # macOS
crontab -l | grep claude-archive           # Linux
sqlite3 ~/claude-archive/sessions.db "SELECT COUNT(*) FROM msg"
```

After 15 min, `sqlite3 ~/claude-archive/sessions.db "SELECT MAX(ts) FROM msg"` advances toward "now".

## Step 3 — Add to `~/.claude/CLAUDE.md`

Paste this near the top of `~/.claude/CLAUDE.md` so every future Claude session knows about the archive:

```markdown
# Cross-session history (use SQLite archive — don't ask the user repeatedly)

All my Claude Code session JSONLs are ingested into ~/claude-archive/sessions.db
(SQLite FTS5 + sqlite-vec, every 15 min via the `crs` Rust binary on launchd / cron / Task Scheduler).
Verbatim user / assistant / tool_use input / tool_result output across all projects, all sessions.

## Schema
msg(session_id, project, seq, ts, role, tool_name, content)
msg_fts = virtual FTS5 over msg.content (tokenize=unicode61)
msg_vec = vec0 cosine (1024-dim bge-m3) — only after running install-semantic.sh

## When to query
- User asks to recall something from a previous session → query DB first, don't say "I don't remember"
- Picking up interrupted work → look up that project's most recent session tail
- Investigating historical config drift → past tool_use Bash + result is ground truth
- Building project mental model → past tool calls beat memory and git log

## How to query
- CLI: `csearch <fts-query> [project-suffix]` (= `crs csearch`) for exact phrase / IP / hostname
       `vsearch '<concept>' [project]` (= `crs vsearch`) for fuzzy / cross-language / synonym
- SQL: `sqlite3 ~/claude-archive/sessions.db "SELECT ... WHERE rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH 'xxx') LIMIT 20"`

FTS5 syntax: phrase `'"..."'`, boolean `A AND B / OR / NOT`, prefix `foo*`. Words with `- / : / .` MUST be phrase-quoted.

## Caveats
- DB is a historical snapshot — verify current state before acting on it
- DB contains sensitive output (passwords / tokens / IPs) — local only
- Memory and DB split: Memory for curated signal, DB for log-style recall
```

---

## Privacy / security

The DB captures **every tool output verbatim**, including:
- `curl -H "Authorization: Bearer xxx"` tokens
- SSH passwords (if passed via stdin / expect)
- Secrets read from `.env`
- Client IP / MAC / device serials

Disposition rules:
1. **Local only** — no rsync, no iCloud, no Dropbox
2. `chmod 600 ~/claude-archive/sessions.db`
3. On Mac handover: **wipe DB**, re-ingest from scratch on the new Mac
4. To share or archive a single session, extract from `~/.claude/projects/<proj>/<uuid>.jsonl` directly and sanitize manually

---

## Verification checklist

After install, all should hold:

- [ ] `~/claude-archive/crs/target/release/crs --help` prints subcommand list
- [ ] `ls -la ~/claude-archive/sessions.db` exists, > 1MB
- [ ] `csearch claude` (or `crs csearch claude`) returns at least one row
- [ ] `launchctl list | grep claude-archive` (macOS) or `crontab -l | grep claude-archive` (Linux) shows the entry
- [ ] `sqlite3 ~/claude-archive/sessions.db "SELECT COUNT(*) FROM msg"` returns N > 0
- [ ] After 15 min, `sqlite3 ~/claude-archive/sessions.db "SELECT MAX(ts) FROM msg"` advances toward "now"
- [ ] In a new Claude session, ask "上週做什麼?" — Claude should query the archive (`vsearch` first if semantic stack installed, otherwise `csearch`) instead of saying "I don't remember"

---

## Windows install path

For Windows users, all the same steps are wrapped in PowerShell:

```powershell
# One-time: allow local script execution
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

cd scripts
.\install.ps1                       # base setup
.\install-semantic.ps1              # OPTIONAL: native Ollama (OllamaSetup.exe)
# or
.\install-semantic-docker.ps1       # OPTIONAL: Docker Desktop variant
```

`install.ps1` parallels `install.sh` step-for-step:

| Step | macOS / Linux | Windows |
|---|---|---|
| Mkdirs | `mkdir -p ~/claude-archive ~/bin` | `New-Item ~/claude-archive ~/bin` |
| Build binary | `cargo build --release` (in `~/claude-archive/crs/`) | same, output `crs.exe` |
| CLI | `~/bin/crs` symlink | `%USERPROFILE%\bin\crs.exe` copy + `csearch.ps1` / `vsearch.ps1` wrappers |
| Tuning | `cp sqliterc.template ~/.sqliterc` | `Copy-Item sqliterc.template $HOME\.sqliterc` |
| Scheduled ingest | launchd plist (macOS) / crontab (Linux) | **Windows Task Scheduler** `ClaudeArchiveIngest` (15-min repetition) calling `crs.exe build` |
| Initial ingest | `crs build --no-embed` | same |
| PATH | `~/bin` | adds `%USERPROFILE%\bin` to user PATH |
| SessionStart hook | jq into `~/.claude/settings.json` | PowerShell into `%USERPROFILE%\.claude\settings.json` |
| PreToolUse preflight hook | `archive-preflight.sh` copied to `~/.claude/hooks/`, registered for Bash + Read | `archive-preflight.ps1` copied to `%USERPROFILE%\.claude\hooks\`, registered for Bash + Read |

Verification on Windows:
```powershell
Get-ScheduledTask -TaskName ClaudeArchiveIngest | Format-List State,LastRunTime,NextRunTime
csearch.ps1 claude
crs --help
```

Prerequisites on Windows:
- Rust toolchain (rustup-init.exe → `rustup default stable`)
- sqlite3.exe in PATH (`winget install -e --id SQLite.SQLite`)
- PowerShell 5.1+ (built in to Windows 10/11)

## Step 4 (optional) — Semantic search via Ollama + sqlite-vec

Adds `vsearch` for concept-level / synonym / cross-language queries. Complements `csearch`, doesn't replace it.

```bash
./scripts/install-semantic.sh
# or for Docker
./scripts/install-semantic-docker.sh
```

This downloads ~1.3 GB (Ollama binary + `bge-m3` model) and kicks off `crs embed-missing` in background (~2-3 hr for ~100k rows on Apple Silicon, Metal-accelerated). Newest rows embed first so fresh conversations are queryable in minutes. **No Python venv** — embedding goes through the same `crs` binary you already built in Step 1.

After install:
```bash
crs vsearch '上次廣播 deny log 怎麼解的'      # concept query, no exact keyword needed
crs vsearch '防火牆規則調整' network          # also matches "firewall policy"
```

Full details and trade-offs: `semantic-search.md`.

## Step 5 (informational) — SessionStart hook

`install.sh` already registered the SessionStart hook in `~/.claude/settings.json`. The hook command is:

```
~/claude-archive/crs/target/release/crs gen-recent 2>/dev/null || true
```

Each `claude` start triggers it; it writes `<project>/memory/auto_recent.md` containing the last-48h messages most semantically related to the project's open `pending` items (KNN over `msg_vec`, cosine ≤ 0.65, top 6 hits). Skip-guard avoids regenerating when neither the pending file nor the DB has changed.

If you skipped semantic install, the hook still runs but the auto_recent.md will note `_(vsearch-since 不可用：crs binary 缺)_` is **not** what you'll see — instead it'll just say `_(無 pending 檔可當 query seed)_` if no pending file exists, or it falls through to whatever the embedded crs path produces (which works fine for empty/text-only fallback).

To regenerate manually for testing:
```bash
CLAUDE_PROJECT_SLUG='-Users-USER-Documents-projects-network' ~/claude-archive/gen-recent-context.sh
# or directly via crs:
crs gen-recent
```

`crs build` calls `gen-recent` for every known project at the end of each ingest run (every 15 min via launchd / Task Scheduler), so long-running sessions also get fresh context.

---

## See also

- `fts5-syntax.md` — FTS5 query language reference
- `tuning.md` — SQLite performance + ANALYZE / VACUUM
- `faq.md` — common questions / errors
- `semantic-search.md` — optional Ollama + sqlite-vec semantic layer
