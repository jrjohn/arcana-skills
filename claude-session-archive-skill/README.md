# claude-session-archive

Cross-session full-text history of every Claude Code conversation, stored locally. Pair this with Memory for a complete recall stack:

- **Memory** = curated signal (identity / traps / invariants — small)
- **This archive** = verbatim log (every command + result, every chat — large, query on demand)

Backed by SQLite + FTS5 with proper tuning. Millisecond queries. Updates every 15 minutes via launchd.

## What it gives you

```bash
csearch ZyXEL                                 # cross-project keyword
csearch '"auto-power-down"' network           # phrase, project-filtered
csearch 'Sophos AND SEDService' network       # boolean
csearch 'somnic*'                             # prefix
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
│   ├── installation-guide.md         # 6-step setup walkthrough
│   ├── fts5-syntax.md                # query language reference
│   ├── tuning.md                     # SQLite performance + maintenance
│   └── faq.md                        # common errors / questions
└── scripts/
    ├── build.py                      # JSONL → SQLite ingest
    ├── csearch                       # CLI helper
    ├── sqliterc.template             # → ~/.sqliterc (CLI auto-applies tuning)
    └── launchd.plist.template        # → ~/Library/LaunchAgents/com.USER.claude-archive.plist
```

## Quick install

```bash
# 1. mkdirs
mkdir -p ~/claude-archive ~/bin

# 2. ingest script
cp scripts/build.py ~/claude-archive/build.py
chmod +x ~/claude-archive/build.py
python3 ~/claude-archive/build.py

# 3. CLI
cp scripts/csearch ~/bin/csearch
chmod +x ~/bin/csearch
echo $PATH | grep -q "$HOME/bin" || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc

# 4. launchd
USER=$(whoami)
sed "s/<USERNAME>/$USER/g" scripts/launchd.plist.template \
  > ~/Library/LaunchAgents/com.${USER}.claude-archive.plist
launchctl load ~/Library/LaunchAgents/com.${USER}.claude-archive.plist

# 5. SQLite tuning
cp scripts/sqliterc.template ~/.sqliterc

# 6. Tell Claude about it (paste snippet from SKILL.md into ~/.claude/CLAUDE.md)
```

For details, see `references/installation-guide.md`.

## Privacy

The DB captures **every tool output verbatim** — including passwords, tokens, API keys, IPs, MACs. Treat it like an SSH key:

- Local only (no rsync, iCloud, Dropbox)
- `chmod 600 ~/claude-archive/sessions.db`
- Wipe on Mac handover

## License / origin

Originally built 2026-04-24 for John Chang's internal IT workflow. Packaged as a generalized skill 2026-04-27. Free to use and modify.
