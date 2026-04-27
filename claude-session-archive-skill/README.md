# claude-session-archive-skill

Cross-session full-text + semantic history of every Claude Code conversation, stored locally. Pair this with Memory for a complete recall stack:

- **Memory** = curated signal (identity / traps / invariants — small)
- **This archive** = verbatim log (every command + result, every chat — large, query on demand)

Backed by SQLite FTS5 (lexical) and optionally Ollama + sqlite-vec (semantic). Millisecond queries. Updates every 15 minutes via launchd.

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
    ├── embed.py                      # OPTIONAL: Ollama embedding helper
    ├── vsearch.py                    # OPTIONAL: semantic search core
    ├── vsearch                       # OPTIONAL: bash wrapper (~/bin/vsearch)
    └── install-semantic.sh           # OPTIONAL: one-shot semantic stack installer
```

## Quick install (base)

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

## Optional: add semantic search

```bash
# One-shot installer: Ollama binary + nomic-embed-text model + venv + scripts + backfill
./scripts/install-semantic.sh
```

After install completes (~30-90 min for 100k rows on Apple Silicon), `vsearch` is ready. See `references/semantic-search.md` for details and trade-offs.

## Privacy

The DB captures **every tool output verbatim** — including passwords, tokens, API keys, IPs, MACs. Treat it like an SSH key:

- Local only (no rsync, iCloud, Dropbox)
- `chmod 600 ~/claude-archive/sessions.db`
- Wipe on Mac handover

## License / origin

Originally built 2026-04-24 for John Chang's internal IT workflow. Packaged as a generalized skill 2026-04-27. Free to use and modify.
