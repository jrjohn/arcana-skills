# FAQ / Troubleshooting

## Q: Does the current session show up immediately?

No. JSONL is written by Claude Code in real time, but the DB is updated only when launchd's 15-minute tick fires. To force-sync:

```bash
python3 ~/claude-archive/build.py
```

Idempotent — only re-ingests files whose mtime changed.

## Q: How do I sync across multiple Macs?

**Don't.** The DB contains every tool output verbatim — passwords, tokens, IPs, internal hostnames. Each Mac should ingest its own JSONLs.

If you really need cross-device search (e.g., laptop + desktop both yours): keep two separate DBs and `csearch` each, or build a privacy-aware merge process. Not part of this skill.

## Q: Should I keep using Memory if I have the archive?

Yes, but with a clear split:
- **Memory** — curated signal that should always be in context: identity, traps, invariants, preferences. Small, hand-curated.
- **Archive** — log-style "what did we do when". Large, machine-generated, queried on demand.

Don't store ephemeral stuff in Memory. Don't try to "curate" the Archive (i.e., don't delete rows to make it more relevant — see the retention rule).

## Q: Will it slow down disk / CPU?

- Ingest runs every 15 min, ~10 sec on a 100k-row DB. Negligible.
- WAL mode means reads aren't blocked.
- FTS5 query is millisecond-level even at GB scale (with cache + mmap tuning).

## Q: Why does `csearch local-in-deny-broadcast` error with "no such column: in"?

FTS5 treats `-` as boolean NOT and `:` as column qualifier. Phrase-quote anything containing them:

```bash
csearch '"local-in-deny-broadcast"' network    # ✓
csearch local-in-deny-broadcast network        # ✗
```

See `fts5-syntax.md` for the full list.

## Q: DB grew to 1GB — is that fine?

Yes. With the default tuning (cache 512MB + mmap 512MB), queries stay millisecond-level. Don't delete old data to "manage size". If absolutely needed, move the dir to external storage.

## Q: Why are my searches returning 0 hits when I know I discussed it?

Common causes (in order of likelihood):

1. **Hyphen / dot in query without quotes** — see above.
2. **Implicit AND across all words** — `csearch foo bar` requires both. Try `'foo OR bar'`.
3. **Wrong project filter** — `csearch X mysub` only matches projects whose slug *contains* `mysub`. Check `sqlite3 ~/claude-archive/sessions.db "SELECT DISTINCT project FROM msg LIMIT 30"` to see slugs.
4. **Ingest hasn't run yet** — current session's JSONL not yet ingested. `python3 ~/claude-archive/build.py`.
5. **Tokenizer differences** — words like `sk-proj-xxx` get tokenized as `sk` + `proj` + `xxx`. Use phrase to bind.

## Q: launchctl load fails with "Bootstrap failed"

Common causes:

- File already loaded — `launchctl unload` first, then re-load
- Permissions on plist not 644 — `chmod 644 ~/Library/LaunchAgents/com.<USER>.claude-archive.plist`
- Path in plist doesn't exist — make sure `/usr/bin/python3` and your `build.py` path are valid

Diagnose:
```bash
launchctl error <last_exit_code>          # explain numeric error
log show --predicate 'subsystem == "com.apple.xpc.launchd"' --last 10m | grep claude-archive
```

## Q: Can I rebuild from scratch?

Yes. `build.py` is idempotent and full rebuild is safe:

```bash
rm ~/claude-archive/sessions.db
python3 ~/claude-archive/build.py    # 30-60 sec
```

You'll lose nothing because `~/.claude/projects/*/*.jsonl` is the source of truth. Don't use this to "reset" — use only if DB is corrupt.

## Q: Can I share a search result with someone?

Result rows contain raw tool output. Sanitize before sharing:

```bash
csearch '<query>' <project> | grep -v -i 'password\|token\|api[_-]key' | less
```

Better: extract from `~/.claude/projects/<proj>/<session-id>.jsonl` directly, which preserves structure for review.

## Q: What if I'm on Linux, not Mac?

Most of this works. Substitutions:
- launchd → systemd timer or cron
- `~/Library/LaunchAgents/...plist` → `~/.config/systemd/user/claude-archive.timer`
- `/usr/bin/python3` path may differ

The `build.py` and `csearch` themselves are POSIX-portable.

## Q: Windows install — what's different?

Use the `.ps1` scripts in `scripts/`:
- `install.ps1` — replaces the bash steps + registers Windows **Task Scheduler** (not launchd)
- `csearch.ps1` / `vsearch.ps1` — PowerShell wrappers (placed in `%USERPROFILE%\bin`, added to PATH)
- `install-semantic.ps1` / `install-semantic-docker.ps1` — Ollama install (native via OllamaSetup.exe, or Docker Desktop)

Common Windows gotchas:
- **Execution Policy blocks .ps1** — run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
- **sqlite3.exe not in PATH** — `winget install -e --id SQLite.SQLite` (or download from sqlite.org and add to PATH manually).
- **Python from Microsoft Store** — installs at a stub path that confuses scripts. Prefer `winget install -e --id Python.Python.3.12` or python.org installer with "Add to PATH" checked.
- **Task Scheduler under Battery** — tasks may be skipped on battery. `install.ps1` sets `-AllowStartIfOnBatteries` to avoid this.
- **Path with spaces** (e.g. `C:\Users\Jane Doe\`) — always quote arguments. `install.ps1` handles this internally; if writing your own scripts, use `"%USERPROFILE%\..."` not bare paths.

Verify Scheduled Task is registered + running:
```powershell
Get-ScheduledTask -TaskName ClaudeArchiveIngest | Format-List State,LastRunTime,NextRunTime,LastTaskResult
```

## Q: How big can this DB get on disk?

Empirically: ~5MB per active workday. Heavy users see ~100MB/month. The schema scales linearly; with current tuning, query latency is flat up to ~10GB.
