---
name: claude-session-archive-skill
description: Cross-platform (macOS / Linux / Windows) cross-session full-text + semantic history of every Claude Code conversation. Ingests all ~/.claude/projects/*/*.jsonl into a local SQLite FTS5 database (~/claude-archive/sessions.db) every 15 minutes (launchd on macOS, Task Scheduler on Windows, cron / systemd on Linux), so any new session can recall verbatim what you did before — across all projects, all sessions, all tool_use inputs and tool_result outputs. Two query modes: `csearch` (FTS5 lexical, exact phrase / boolean / prefix) and optionally `vsearch` (semantic via Ollama + sqlite-vec + nomic-embed-text — concept queries, synonym / cross-language matching). Activates when user wants to (a) install the archive on a new machine (macOS/Linux/Windows), (b) query past sessions ("上週/昨天/之前做了什麼", "csearch ...", "vsearch ...", "查歷史對話 / past conversations / semantic search"), (c) install or troubleshoot Ollama / sqlite-vec semantic stack, (d) tune SQLite performance, or (e) troubleshoot FTS5 syntax / ingest issues.
version: 1.0.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Claude Session Archive

Permanent, local, full-text searchable history of every Claude Code session you've ever run on this Mac. Pairs with Memory: Memory holds curated signal (identity, traps, invariants); this archive holds the verbatim log (what you actually did, when, with what command and what result).

## When to use this skill

| Trigger | Action |
|---|---|
| User asks you to recall something from a past session ("上週那個 X 怎麼設的？", "we discussed Y last Thursday") | Run `csearch '<keywords>' [project]` first, then summarize from the hit |
| User invokes `/claude-session-archive-skill` or types `csearch ...` and it errors | Diagnose: archive not installed yet → walk through install. Already installed → check FTS5 syntax. |
| User on a fresh Mac wants the archive set up | Walk through Steps 1-6 in `references/installation-guide.md` |
| User reports queries are slow or DB grew large | See `references/tuning.md` |
| User asks a one-shot historical question ("when did port X get shut down?", "what password did we use for device Y?") | Use direct `sqlite3` SQL — see `references/fts5-syntax.md` for boolean / phrase / prefix patterns |

## How it works (architecture)

```
~/.claude/projects/*/*.jsonl    ← Claude Code writes session JSONL (automatic)
            │
            ▼  build.py (idempotent incremental ingest)
~/claude-archive/sessions.db    ← SQLite + FTS5 virtual table
            │  (launchd every 15 min)
            ├── ~/bin/csearch                  CLI helper
            ├── sqlite3 <db> "SELECT ..."      raw SQL
            ├── ~/.sqliterc                    cache=512MB / mmap=512MB tuning
            └── ~/.claude/CLAUDE.md            instructions so any new Claude
                                               session knows to query first
```

DB schema:
```sql
msg(session_id, project, seq, ts, role, tool_name, content)  -- main table
msg_fts                                                      -- FTS5 over content
ingest_state(file_path, mtime, lines)                        -- incremental tracking
```

## Quick install — pick your OS

Detailed instructions in `references/installation-guide.md`.

### macOS / Linux (bash)

```bash
cd scripts
mkdir -p ~/claude-archive ~/bin
cp build.py ~/claude-archive/ ; chmod +x ~/claude-archive/build.py
cp csearch ~/bin/ ; chmod +x ~/bin/csearch
cp sqliterc.template ~/.sqliterc
USER=$(whoami)
sed "s/<USERNAME>/$USER/g" launchd.plist.template > ~/Library/LaunchAgents/com.${USER}.claude-archive.plist
launchctl load ~/Library/LaunchAgents/com.${USER}.claude-archive.plist
python3 ~/claude-archive/build.py
# (Optional) semantic search:
./install-semantic.sh        # native Ollama
# or
./install-semantic-docker.sh # Docker container
```

### Windows (PowerShell)

```powershell
# Allow local script execution once:
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# Then from inside scripts/:
.\install.ps1                # base: build.py + csearch.ps1 + Scheduled Task
.\install-semantic.ps1       # OPTIONAL: native Ollama + vsearch.ps1
# or
.\install-semantic-docker.ps1  # OPTIONAL: Ollama in Docker Desktop
```

Then in any new Claude session add the snippet at the bottom of this file to `~/.claude/CLAUDE.md` (or `%USERPROFILE%\.claude\CLAUDE.md`) so Claude knows to query the DB.

## Daily usage patterns

### CLI — `csearch` (FTS5 lexical, always available)

```bash
# 簡單關鍵字
csearch ZyXEL

# Phrase（含 - / : / . 必須用 phrase）
csearch '"auto-power-down"' network

# Boolean
csearch 'Sophos AND SEDService' network
csearch 'Sophos OR Bitdefender'

# Prefix
csearch 'somnic*'

# 限定 project（slug 部分匹配）
csearch FortiGate network
```

### CLI — `vsearch` (semantic, optional Step 7)

```bash
# Concept search without remembering specific keywords
vsearch '上次廣播 deny log 太多怎麼解的'

# Cross-language: 防火牆 finds firewall
vsearch '防火牆規則調整' network

# Vague description
vsearch 'wireless AP keeps disconnecting' network
```

When to pick which:
- **csearch** — you remember a specific phrase / IP / hostname
- **vsearch** — you forgot the exact wording, or need synonym / cross-language matching

### Direct SQL (for complex queries)

```sql
sqlite3 ~/claude-archive/sessions.db "
SELECT session_id, substr(ts,1,19), role, substr(content,1,200)
FROM msg
WHERE project LIKE '%network%'
  AND date(ts) = '2026-04-23'
  AND rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH 'shaper quota')
ORDER BY ts LIMIT 20"
```

## Critical guidance

**1. Never delete old rows.** The whole point is permanent memory. If disk gets tight, move `~/claude-archive/` to external storage (edit `DB_DIR` in `build.py`), don't `DELETE FROM msg WHERE ts < ...`. Losing history defeats the purpose.

**2. FTS5 hyphen / colon trap.** FTS5 treats `-`, `:`, `.` as boolean / column operators. Anything containing them must be quoted as a phrase:
```bash
csearch '"local-in-deny-broadcast"' network    # ✓ works
csearch 'local-in-deny-broadcast' network      # ✗ error: "no such column: in"
```

**3. DB is sensitive.** It captures every tool output verbatim — including passwords, tokens, API keys, IPs, MACs. Keep `chmod 600`, never sync to iCloud / rsync / Dropbox. On Mac handover, wipe and re-ingest.

**4. Memory and DB have different roles.** Memory = curated signal (identity, traps, invariants — small). DB = verbatim log (any-time-any-detail recall — large). Don't write log facts to Memory; don't curate the DB.

**5. Ingest is incremental + idempotent.** `build.py` uses (file path, mtime) tracking — re-running is safe and only re-reads changed JSONLs. New session content lands in DB at next 15-min launchd tick (or run manually for instant indexing).

## Snippet for `~/.claude/CLAUDE.md`

Paste this near the top so every Claude session knows about the archive:

```markdown
# Cross-session history (use SQLite archive — don't ask the user repeatedly)

All my Claude Code session JSONLs are ingested into ~/claude-archive/sessions.db
(SQLite FTS5, every 15 min via launchd). It contains verbatim user / assistant /
tool_use input / tool_result output across all projects, all sessions.

## Schema
msg(session_id, project, seq, ts, role, tool_name, content)
msg_fts = virtual FTS5 over msg.content (tokenize=unicode61)

## When to query
- User asks to recall something from a previous session → query DB first, don't say "I don't remember"
- Picking up interrupted work ("continue from before") → look up that project's most recent session tail
- Investigating historical config drift ("when did port X go down?") → past tool_use Bash + result is ground truth
- Building project mental model → past tool calls beat memory (more complete) and git log (more immediate)

## How to query
- CLI: `csearch <fts-query> [project-suffix]`
- SQL: `sqlite3 ~/claude-archive/sessions.db "SELECT ... WHERE rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH 'xxx') LIMIT 20"`

FTS5 syntax: phrase `'"..."'`, boolean `A AND B / OR / NOT`, prefix `foo*`. Words with `- / : / .` MUST be phrase-quoted.

## Caveats
- DB is a historical snapshot — always verify current state (file content, live config) before acting on it
- DB contains sensitive output (passwords / tokens / IPs) — local only, no sharing
- Memory and DB split: Memory for curated signal, DB for log-style recall
```

## Files in this skill

```
claude-session-archive-skill/
├── SKILL.md                          # this file
├── README.md                         # human-friendly intro
├── references/
│   ├── installation-guide.md         # detailed step-by-step setup
│   ├── fts5-syntax.md                # FTS5 query language reference
│   ├── tuning.md                     # SQLite performance + maintenance
│   ├── faq.md                        # common questions / troubleshooting
│   └── semantic-search.md            # OPTIONAL: Ollama + sqlite-vec for vsearch
└── scripts/
    ├── build.py                      # ingest script (~/claude-archive/build.py)
    ├── csearch                       # CLI helper (~/bin/csearch)
    ├── sqliterc.template             # → ~/.sqliterc
    ├── launchd.plist.template        # → ~/Library/LaunchAgents/...
    ├── embed.py                      # OPTIONAL: Ollama embedding helper (cross-platform Python)
    ├── vsearch.py                    # OPTIONAL: semantic search Python core (cross-platform)
    ├── vsearch                       # OPTIONAL: bash wrapper (~/bin/vsearch)
    ├── vsearch.ps1                   # OPTIONAL Windows: PowerShell wrapper
    ├── csearch.ps1                   # Windows: PowerShell csearch wrapper
    ├── install.ps1                   # Windows: base installer (mkdir + scheduled task + sqliterc)
    ├── install-semantic.ps1          # Windows OPTIONAL: native Ollama + vsearch
    ├── install-semantic-docker.ps1   # Windows OPTIONAL: Docker Ollama variant
    ├── install-semantic.sh           # macOS/Linux OPTIONAL: native Ollama installer
    ├── install-semantic-docker.sh    # macOS/Linux OPTIONAL: Docker Ollama installer
    └── ollama.plist.template         # macOS OPTIONAL: launchd auto-start template
```

## Author / version

- 2026-04-24 v1.0 initial setup (John Chang)
- 2026-04-27 v1.0.0 packaged as skill, with SQLite tuning (cache 512MB, mmap, temp_store=MEMORY)
- 2026-04-27 v1.1.0 optional semantic search: Ollama + sqlite-vec + nomic-embed-text + `vsearch`
- 2026-04-27 v1.2.0 native Windows support: csearch.ps1 / vsearch.ps1 / install.ps1 / install-semantic.ps1 / install-semantic-docker.ps1 + Scheduled Task instead of launchd
