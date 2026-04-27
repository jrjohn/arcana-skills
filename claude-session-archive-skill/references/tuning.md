# Performance Tuning + Maintenance

## Default tuning (already applied via this skill)

| PRAGMA | Default | After install | Reason |
|---|---|---|---|
| `journal_mode` | DELETE | **WAL** | Concurrent reads while ingest writes |
| `synchronous` | FULL | **NORMAL** | Faster writes (safe with WAL) |
| `cache_size` | -2000 (~8MB) | **-524288 (512MB)** | Whole DB fits in RAM up to ~1GB |
| `mmap_size` | 0 | **536870912 (512MB)** | Zero-copy reads |
| `temp_store` | DEFAULT | **MEMORY** | Sorts / temp tables in RAM |

These are set in two places:
1. **`build.py`** — applied on every ingest (so launchd benefits)
2. **`~/.sqliterc`** — auto-applied to every `sqlite3` CLI invocation (`csearch`, ad-hoc queries)

## Verify

```bash
for p in cache_size mmap_size temp_store journal_mode synchronous; do
  V=$(sqlite3 ~/claude-archive/sessions.db "PRAGMA $p")
  echo "  $p = $V"
done
```

Expected:
```
  cache_size = -524288
  mmap_size = 536870912
  temp_store = 2
  journal_mode = wal
  synchronous = 1
```

## Memory budget

512MB cache + 512MB mmap = up to **1GB** virtual memory used by `sqlite3` per connection. On a 16GB+ Mac this is negligible. mmap is virtual — actual physical pages are paged in by the kernel on touch.

If you have a constrained machine (8GB RAM and many other apps), halve them:

```
PRAGMA cache_size = -262144;     -- 256MB
PRAGMA mmap_size  = 268435456;   -- 256MB
```

## Periodic maintenance

### ANALYZE (occasional, recommended)

After significant data growth (monthly, or after row count doubles):

```bash
sqlite3 ~/claude-archive/sessions.db "ANALYZE; PRAGMA optimize;"
```

Updates query planner stats. Usually < 1 second. Lets SQLite pick better indexes.

### VACUUM (rare)

After large deletes (which you shouldn't do — see `installation-guide.md` privacy section). Reclaims unused page space. Locks the DB while running. Don't run during ingest:

```bash
launchctl unload ~/Library/LaunchAgents/com.<USER>.claude-archive.plist
sqlite3 ~/claude-archive/sessions.db "VACUUM"
launchctl load ~/Library/LaunchAgents/com.<USER>.claude-archive.plist
```

### Don't auto-rotate

**Never** `DELETE FROM msg WHERE ts < ...` — losing old rows defeats the entire "permanent memory" goal. If disk fills:

1. Move the DB to external storage:
   ```bash
   # 1. Stop launchd
   launchctl unload ~/Library/LaunchAgents/com.<USER>.claude-archive.plist
   
   # 2. Move
   mv ~/claude-archive /Volumes/External/claude-archive
   ln -s /Volumes/External/claude-archive ~/claude-archive
   
   # 3. Restart launchd
   launchctl load ~/Library/LaunchAgents/com.<USER>.claude-archive.plist
   ```
2. Or edit `~/claude-archive/build.py` `DB_DIR` to point at the new location and update the launchd plist accordingly.

## Benchmark

On a 32GB Mac with ~100k rows / 186MB DB (warm cache):

| Query | Time |
|---|---|
| FTS phrase (`'sslvpn AND deny'`) | ~5-10 ms |
| 3-word boolean | ~5 ms |
| Project + date range scan | ~5-10 ms |
| Combined FTS + project + date | ~10 ms |
| `csearch '<query>' <project>` end-to-end | ~10-15 ms |

These remain millisecond-level up to ~1GB DB size with current tuning.

## Indexes

`build.py` creates these (idempotent):

```sql
PRIMARY KEY (session_id, seq)        -- main lookup
idx_msg_ts                            -- time-based queries
idx_msg_project (project, ts)         -- per-project time slices
idx_msg_tool                          -- "find Bash invocations"
msg_fts                               -- full-text on content
```

Don't add more indexes without a query that needs them — they slow down ingest.
