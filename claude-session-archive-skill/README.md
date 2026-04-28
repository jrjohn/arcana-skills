# claude-session-archive-skill

Cross-session full-text + semantic history of every Claude Code conversation, stored locally. Pair this with Memory for a complete recall stack:

- **Memory** = curated signal (identity / traps / invariants — small)
- **This archive** = verbatim log (every command + result, every chat — large, query on demand)

Backed by SQLite FTS5 (lexical) and optionally Ollama + sqlite-vec (semantic, **bge-m3** 1024-dim, multilingual SOTA). Millisecond queries. Updates every 15 minutes via launchd / Task Scheduler.

## What it gives you

### `csearch` — FTS5 lexical (always available)
```bash
csearch ZyXEL                                 # cross-project keyword
csearch '"auto-power-down"' network           # phrase, project-filtered
csearch 'Sophos AND SEDService' network       # boolean
csearch 'somnic*'                             # prefix
```

### `vsearch` — semantic (optional Step 7)
```bash
vsearch '上次廣播 deny log 怎麼解的'           # concept query, no exact keyword
vsearch '防火牆規則調整' network              # also matches "firewall policy"
vsearch 'wireless AP keeps dropping' network  # vague description still works
```

Inside Claude:
> User: "上週那個 FortiGate shaper 怎麼設的？"
> Claude: *(silently runs `csearch 'shaper' network`, reads the actual session, reports back)*

## What's in this skill

```
claude-session-archive-skill/
├── SKILL.md                          # Skill entry — read this first
├── README.md                         # this file
├── references/
│   ├── installation-guide.md         # 6-step base setup walkthrough
│   ├── fts5-syntax.md                # FTS5 query language reference
│   ├── tuning.md                     # SQLite performance + maintenance
│   ├── faq.md                        # common errors / questions
│   └── semantic-search.md            # OPTIONAL: Ollama + sqlite-vec for vsearch
└── scripts/
    ├── build.py                      # JSONL → SQLite ingest (with embed hook)
    ├── csearch                       # CLI lexical search
    ├── sqliterc.template             # → ~/.sqliterc (SQLite tuning)
    ├── launchd.plist.template        # → ~/Library/LaunchAgents/com.USER.claude-archive.plist
    ├── embed.py                      # OPTIONAL: Ollama embedding helper (cross-platform)
    ├── embed_parallel.py             # OPTIONAL: parallel backfill (8 workers, 4-5x faster)
    ├── vsearch.py                    # OPTIONAL: semantic search core (cross-platform)
    │
    │  # macOS / Linux
    ├── vsearch                       # OPTIONAL: bash wrapper (~/bin/vsearch)
    ├── install-semantic.sh           # OPTIONAL: native binary installer
    ├── install-semantic-docker.sh    # OPTIONAL: Docker container installer
    ├── ollama.plist.template         # OPTIONAL: launchd auto-start (macOS)
    │
    │  # Windows
    ├── csearch.ps1                   # PowerShell csearch wrapper
    ├── vsearch.ps1                   # OPTIONAL: PowerShell vsearch wrapper
    ├── install.ps1                   # base installer (build.py + Scheduled Task)
    ├── install-semantic.ps1          # OPTIONAL: native Ollama (OllamaSetup.exe)
    └── install-semantic-docker.ps1   # OPTIONAL: Docker Desktop variant
```

## Quick install — pick your OS

### macOS / Linux (bash)

```bash
cd scripts
mkdir -p ~/claude-archive ~/bin
cp build.py ~/claude-archive/build.py    && chmod +x ~/claude-archive/build.py
cp csearch  ~/bin/csearch                && chmod +x ~/bin/csearch
cp sqliterc.template ~/.sqliterc
echo $PATH | grep -q "$HOME/bin" || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc

# launchd auto-ingest @ 15 min
USER=$(whoami)
sed "s/<USERNAME>/$USER/g" launchd.plist.template > ~/Library/LaunchAgents/com.${USER}.claude-archive.plist
launchctl load ~/Library/LaunchAgents/com.${USER}.claude-archive.plist

# first ingest
python3 ~/claude-archive/build.py
```

### Windows (PowerShell)

```powershell
# One-time: allow local script execution
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

cd scripts
.\install.ps1
# That single script does: mkdirs → copy build.py / csearch.ps1 / sqliterc → register
# Scheduled Task "ClaudeArchiveIngest" (15 min) → run first ingest → add %USERPROFILE%\bin to PATH
```

Then for both: paste the snippet from `SKILL.md` into `~/.claude/CLAUDE.md` (or `%USERPROFILE%\.claude\CLAUDE.md` on Windows) so future Claude sessions know to query the DB.

For details, see `references/installation-guide.md`.

## Optional: add semantic search

```bash
# macOS / Linux
./scripts/install-semantic.sh           # native Ollama binary
./scripts/install-semantic-docker.sh    # Docker variant
```

```powershell
# Windows
.\scripts\install-semantic.ps1          # native Ollama (downloads OllamaSetup.exe)
.\scripts\install-semantic-docker.ps1   # Docker Desktop variant
```

After install completes (~1 hr native / ~3-5 hr Docker on macOS for 100k rows), `vsearch` / `vsearch.ps1` is ready. See `references/semantic-search.md` for details and trade-offs.

## Privacy

The DB captures **every tool output verbatim** — including passwords, tokens, API keys, IPs, MACs. Treat it like an SSH key:

- Local only (no rsync, iCloud, Dropbox)
- `chmod 600 ~/claude-archive/sessions.db`
- Wipe on Mac handover

## License / origin

Originally built 2026-04-24 for John Chang's internal IT workflow. Packaged as a generalized skill 2026-04-27. Free to use and modify.
