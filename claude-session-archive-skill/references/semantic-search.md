# Semantic Search (Optional) — Ollama + sqlite-vec

The base skill ships with `csearch` (FTS5 lexical). For **concept-level / synonym / cross-language** queries, this optional add-on gives you `vsearch` backed by local embeddings.

## What you gain

| Need | csearch (FTS5) | vsearch (semantic) |
|---|---|---|
| Find exact phrase / IP / hostname | ✅ | weak |
| "上次討論 X 怎麼解的" without remembering keywords | ❌ | ✅ |
| 中英對照（`防火牆` 找到 `firewall`） | ❌ | ✅ |
| Concept query (`找權限管理相關決策`) | ❌ | ✅ |
| Speed | ~10 ms | ~50–150 ms |
| Privacy | 100% local | 100% local (Ollama) |

`vsearch` complements, doesn't replace `csearch`. Use both.

## Architecture

```
~/.claude/projects/*/*.jsonl
       │
       ▼  build.py (ingest text + call embed_missing)
~/claude-archive/sessions.db
       ├── msg            FTS5 indexed (csearch)
       └── msg_vec        vec0 + nomic-embed-text (vsearch)
                          768-dim, cosine distance
                                       │
                                       ▼
                          Ollama @ localhost:11434
                          (nomic-embed-text, 274 MB, runs entirely locally)
```

## One-time install (Step 7 of installation-guide.md)

```bash
# 1. Ollama daemon
# Either install via brew (slow, pulls mlx) or download binary directly:
curl -fL https://github.com/ollama/ollama/releases/latest/download/ollama-darwin.tgz \
  -o /tmp/ollama.tgz
mkdir -p ~/claude-archive/ollama-bin
tar -xzf /tmp/ollama.tgz -C ~/claude-archive/ollama-bin
ln -sf ~/claude-archive/ollama-bin/ollama ~/bin/ollama

# Run as background daemon (one-shot)
nohup ~/bin/ollama serve > ~/claude-archive/ollama.log 2>&1 &

# Or register with launchd for auto-start at login + restart on crash:
USER=$(whoami)
sed "s|<USERNAME>|$USER|g" scripts/ollama.plist.template \
  > ~/Library/LaunchAgents/com.${USER}.ollama.plist
launchctl load ~/Library/LaunchAgents/com.${USER}.ollama.plist

# 2. Pull embedding model (~274 MB)
ollama pull nomic-embed-text

# 3. Python venv with sqlite-vec + requests
python3 -m venv ~/claude-archive/.venv
~/claude-archive/.venv/bin/pip install sqlite-vec requests

# 4. Install scripts
cp scripts/embed.py    ~/claude-archive/embed.py
cp scripts/vsearch.py  ~/claude-archive/vsearch.py
cp scripts/vsearch     ~/bin/vsearch
chmod +x ~/bin/vsearch ~/claude-archive/embed.py ~/claude-archive/vsearch.py

# 5. Backfill embeddings for existing rows (~46 min for 96k rows on M-series)
~/claude-archive/.venv/bin/python ~/claude-archive/embed.py
# Outputs: progress every 500 rows, e.g.
#   embedding 96000 rows via nomic-embed-text...
#     500/96000  rate=33.0/s  eta=48.4 min
#     1000/96000 rate=33.5/s  eta=47.2 min
#     ...
#   embedded 96000 rows in 47.8 min  (skipped 0 empty)

# 6. Confirm
sqlite3 ~/claude-archive/sessions.db "
  SELECT (SELECT COUNT(*) FROM msg) AS msgs,
         (SELECT COUNT(*) FROM msg_vec) AS vecs
"
```

## Ongoing operation

- `build.py` calls `maybe_embed_new()` after ingest. If Ollama is reachable + `embed.py` is importable, it embeds new rows; otherwise silent no-op.
- Each new row costs ~30 ms during ingest (negligible at 15-min cadence).
- launchd doesn't need any change — same plist, same schedule.

## vsearch usage

```bash
# Concept search (no specific keyword needed)
vsearch '上次廣播 deny log 太多怎麼解的'
vsearch 'how did we set up shaper for video calls' network

# Cross-language
vsearch '防火牆規則調整'                # also finds "FortiGate policy edit"
vsearch 'wireless access point issues'  # also finds "UniFi AP 重連"

# Vague description
vsearch '客戶反應網路慢的處理流程'
```

## Compare to FTS5 on the same query

```bash
csearch 'broadcast deny'         # only matches rows literally containing both words
vsearch 'broadcast deny'         # also matches rows about "NetBIOS noise" / "local-in policy" / "log flood"
```

Use both:
1. `csearch` first (free, instant, no Ollama dependency)
2. `vsearch` as fallback when keywords don't match

## Schema additions

```sql
-- Created automatically by ensure_vec_schema()
CREATE VIRTUAL TABLE msg_vec USING vec0(
    embedding float[768] distance_metric=cosine
);
-- rowid links to msg.rowid (1:1, sparse — only embedded rows present)
```

## Disk impact

- `nomic-embed-text` model: 274 MB on disk (~/.ollama/models/)
- `msg_vec` table: ~3 KB / row (768 floats × 4 bytes + overhead)
  - 96k rows ≈ 290 MB
  - 1M rows ≈ 3 GB

Compared to `msg` + FTS5 currently ~186 MB, the semantic stack roughly doubles DB size at current row count.

## Memory while running

- Ollama daemon: ~500 MB resident (model loaded)
- Python query: ~100 MB during search (mmap dominates)
- Together: < 1 GB. On a 16GB+ Mac, irrelevant.

## Performance characteristics

| Component | Cold | Hot |
|---|---|---|
| Ollama embed (single) | 50-100 ms | 14-25 ms |
| sqlite-vec KNN over 96k rows | ~30-80 ms (brute force) | same |
| msg JOIN | < 5 ms | < 5 ms |
| **Total `vsearch` end-to-end** | ~150 ms | **~50-150 ms** |

Ollama keeps the model resident after first use for ~5 min idle (configurable). For frequent use, single calls stay in the warm path.

## Scaling beyond 1M rows

sqlite-vec uses brute-force KNN (no ANN index). At ~10x current scale (1M rows ≈ 3 GB vec table), KNN time goes to ~1 sec. If you reach that scale, options:

1. Switch to FAISS or hnswlib outside SQLite
2. Use sqlite-vec's upcoming ANN modes (HNSW being added)
3. Pre-filter with FTS5 + project + date to a smaller candidate set, then KNN

For now (≤1M rows) brute force is plenty.

## Disabling / removing

```bash
# Stop Ollama (if managed by launchd, unload first)
USER=$(whoami)
launchctl unload ~/Library/LaunchAgents/com.${USER}.ollama.plist 2>/dev/null
rm -f ~/Library/LaunchAgents/com.${USER}.ollama.plist
pkill -f 'ollama serve'

# Drop vec table (preserves msg / FTS5)
sqlite3 ~/claude-archive/sessions.db "DROP TABLE msg_vec"

# Remove model + binary if reclaiming disk
rm -rf ~/.ollama ~/claude-archive/ollama-bin

# build.py's maybe_embed_new() is silent no-op if embed.py / Ollama missing
```

`csearch` and the rest of the skill keep working unchanged.

## Why nomic-embed-text?

- 768-dim, fast (~20 ms / call on Apple Silicon)
- Multilingual (中英 mix works)
- 274 MB model — small footprint
- Free, runs locally

Alternatives if you want to swap:
- `mxbai-embed-large` — 1024-dim, slightly better quality, ~700 MB, ~1.5x slower
- `bge-m3` — strong multilingual, larger
- OpenAI `text-embedding-3-small` — but DB content goes to OpenAI = privacy violation

Edit `EMBED_MODEL` and `EMBED_DIM` in `embed.py` to change. After change, drop `msg_vec` and re-backfill (different model = different vector space, can't mix).
