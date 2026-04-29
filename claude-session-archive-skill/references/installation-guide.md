# Installation Guide — Claude Session Archive

Detailed step-by-step setup. For the conceptual overview see `../SKILL.md`.

## Layered design

| Layer | Purpose | Maintained by |
|---|---|---|
| **JSONL** (`~/.claude/projects/*/*.jsonl`) | Raw verbatim per-session log | Claude Code (automatic) |
| **SQLite FTS5** (`~/claude-archive/sessions.db`) | Cross-session full-text index | This skill (launchd every 15 min) |
| **Memory** (`~/.claude/projects/*/memory/`) | Curated signal: identity, traps, invariants | Claude (writes when learning something durable) |

## Architecture

```
~/.claude/projects/*/*.jsonl        (Claude Code writes automatically)
              │
              ▼ build.py (incremental, idempotent)
~/claude-archive/sessions.db        (SQLite + FTS5)
              │
              ├── ~/bin/csearch                   CLI helper
              ├── sqlite3 <db> "SELECT ..."       direct SQL
              ├── ~/.sqliterc                    cache/mmap/temp_store tuning
              └── ~/.claude/CLAUDE.md             instructions for future Claude
```

DB schema:
```sql
msg(session_id, project, seq, ts, role, tool_name, content)  PRIMARY KEY (session_id, seq)
msg_fts                  -- virtual FTS5 over content, tokenize=unicode61
ingest_state(file_path, mtime, lines)
```

---

## Step 1 — Mkdirs

```bash
mkdir -p ~/claude-archive ~/bin
```

## Step 2 — Place ingest script

Copy `scripts/build.py` to `~/claude-archive/build.py`:

```bash
cp scripts/build.py ~/claude-archive/build.py
chmod +x ~/claude-archive/build.py
python3 ~/claude-archive/build.py    # first ingest, ~30 sec
```

Output should look like:
```
  +XXXX  -Users-USER-Documents-projects-foo/abc123.jsonl
  ...
touched N files, +M rows
DB total: M rows / S sessions / P projects
DB path: /Users/USER/claude-archive/sessions.db (XX.X MB)
```

## Step 3 — Place CLI helper

Copy `scripts/csearch` to `~/bin/csearch`:

```bash
cp scripts/csearch ~/bin/csearch
chmod +x ~/bin/csearch

# Make sure ~/bin is in PATH (zsh):
echo $PATH | grep -q "$HOME/bin" || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Smoke test:
csearch claude
```

## Step 4 — Register launchd auto-ingest

Copy `scripts/launchd.plist.template` to `~/Library/LaunchAgents/`, replacing `<USERNAME>` with your macOS short username (e.g. `whoami`):

```bash
USER=$(whoami)
sed "s/<USERNAME>/$USER/g" scripts/launchd.plist.template \
  > ~/Library/LaunchAgents/com.${USER}.claude-archive.plist

launchctl load ~/Library/LaunchAgents/com.${USER}.claude-archive.plist
launchctl list | grep claude-archive    # confirm presence
```

## Step 5 — Place `~/.sqliterc`

```bash
cp scripts/sqliterc.template ~/.sqliterc
```

Verify SQLite picks up the tuning:
```bash
sqlite3 ~/claude-archive/sessions.db "PRAGMA cache_size"   # → -524288
sqlite3 ~/claude-archive/sessions.db "PRAGMA mmap_size"    # → 536870912
sqlite3 ~/claude-archive/sessions.db "PRAGMA temp_store"   # → 2 (MEMORY)
```

## Step 6 — Add to `~/.claude/CLAUDE.md`

Paste this near the top of `~/.claude/CLAUDE.md` so every future Claude session knows about the archive:

```markdown
# Cross-session history (use SQLite archive — don't ask the user repeatedly)

All my Claude Code session JSONLs are ingested into ~/claude-archive/sessions.db
(SQLite FTS5, every 15 min via launchd). Verbatim user / assistant /
tool_use input / tool_result output across all projects, all sessions.

## Schema
msg(session_id, project, seq, ts, role, tool_name, content)
msg_fts = virtual FTS5 over msg.content (tokenize=unicode61)

## When to query
- User asks to recall something from a previous session → query DB first, don't say "I don't remember"
- Picking up interrupted work → look up that project's most recent session tail
- Investigating historical config drift → past tool_use Bash + result is ground truth
- Building project mental model → past tool calls beat memory and git log

## How to query
- CLI: `csearch <fts-query> [project-suffix]`
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

- [ ] `ls -la ~/claude-archive/sessions.db` exists, > 1MB
- [ ] `csearch claude` returns at least one row
- [ ] `launchctl list | grep claude-archive` shows the agent
- [ ] `sqlite3 ~/claude-archive/sessions.db "SELECT COUNT(*) FROM msg"` returns N > 0
- [ ] After 15 min, `sqlite3 ~/claude-archive/sessions.db "SELECT MAX(ts) FROM msg"` advances toward "now"
- [ ] In a new Claude session, ask "上週做什麼?" — Claude should `csearch` first instead of saying "I don't remember"

---

## Windows install path

For Windows users, all the same steps are wrapped in PowerShell scripts. Run from inside cloned `claude-session-archive-skill/scripts/`:

```powershell
# One-time: allow local script execution
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# Base setup (build.py + csearch.ps1 + Scheduled Task @ 15 min)
.\install.ps1

# OPTIONAL: semantic search
.\install-semantic.ps1            # native Ollama Windows installer
# or
.\install-semantic-docker.ps1     # Docker Desktop variant
```

What `install.ps1` does (parallel to Steps 1-5 above):

| Step | Linux/macOS | Windows |
|---|---|---|
| Mkdirs | `mkdir -p ~/claude-archive ~/bin` | `New-Item ~/claude-archive ~/bin` |
| Ingest script | `cp build.py ~/claude-archive/` | `Copy-Item build.py %USERPROFILE%\claude-archive\` |
| CLI helper | `cp csearch ~/bin/` | `Copy-Item csearch.ps1 %USERPROFILE%\bin\` |
| Tuning | `cp sqliterc.template ~/.sqliterc` | `Copy-Item sqliterc.template $HOME\.sqliterc` |
| Scheduled ingest | launchd plist | **Windows Task Scheduler** `ClaudeArchiveIngest` (15-min repetition) |
| Initial ingest | `python3 ~/claude-archive/build.py` | `python %USERPROFILE%\claude-archive\build.py` |
| PATH | `~/bin` | adds `%USERPROFILE%\bin` to user PATH |

Verification on Windows:
```powershell
Get-ScheduledTask -TaskName ClaudeArchiveIngest | Format-List State,LastRunTime,NextRunTime
csearch.ps1 claude
```

Prerequisites on Windows:
- Python 3.11+ in PATH (`python --version`)
- sqlite3.exe in PATH (`winget install -e --id SQLite.SQLite`)
- PowerShell 5.1+ (built in to Windows 10/11)

## Step 7 (optional) — Semantic search via Ollama + sqlite-vec

Adds `vsearch` for concept-level / synonym / cross-language queries. Complements `csearch`, doesn't replace it.

```bash
./scripts/install-semantic.sh
```

This downloads ~1.3 GB (Ollama binary + `bge-m3` model), creates a Python venv, installs `embed.py` / `embed_parallel.py` / `vsearch.py` / `vsearch` CLI, and kicks off parallel backfill (8 workers). Backfill runs ~2-3 hr in background for ~100k rows on Apple Silicon (Metal-accelerated).

After install:
```bash
vsearch '上次廣播 deny log 怎麼解的'        # concept query, no exact keyword needed
vsearch '防火牆規則調整' network            # also matches "firewall policy"
```

Full details and trade-offs: `semantic-search.md`.

## Step 8 (optional, recommended) — SessionStart hook for auto_recent.md

Bridges session.db → Memory: every `claude` start, a hook regenerates `<project>/memory/auto_recent.md` containing pending + last 48h conversation events.

If you ran `install-semantic.sh`, this is **already done** (auto-registered via jq).

For manual setup:

```bash
# 1. Place script
cp scripts/gen-recent-context.sh ~/claude-archive/gen-recent-context.sh
chmod +x ~/claude-archive/gen-recent-context.sh

# 2. Add SessionStart hook to ~/.claude/settings.json
jq --arg cmd "$HOME/claude-archive/gen-recent-context.sh 2>/dev/null || true" \
   '.hooks.SessionStart = ((.hooks.SessionStart // []) + [{"hooks":[{"type":"command","command":$cmd,"timeout":30}]}])' \
   ~/.claude/settings.json > ~/.claude/settings.json.tmp && mv ~/.claude/settings.json.tmp ~/.claude/settings.json

# 3. Add auto_recent.md to MEMORY.md index for each project
echo '- [自動最近 context](auto_recent.md) — auto-generated by SessionStart hook' \
  >> ~/.claude/projects/<slug>/memory/MEMORY.md
```

`build.py` already calls `gen-recent-context.sh` for every known project at the end of each ingest run (every 15 min via launchd / Task Scheduler), so long-running sessions also get fresh context. No additional setup needed.

Verify:
```bash
# Manual trigger to test
CLAUDE_PROJECT_SLUG='-Users-jrjohn-Documents-projects-network' ~/claude-archive/gen-recent-context.sh

# Open a new claude session, ask "目前 pending 有什麼？" — Claude should answer immediately
# without csearch (the answer is in auto_recent.md → Memory)
```

---

## See also

- `fts5-syntax.md` — FTS5 query language reference
- `tuning.md` — SQLite performance + ANALYZE / VACUUM
- `faq.md` — common questions / errors
- `semantic-search.md` — optional Ollama + sqlite-vec semantic layer
