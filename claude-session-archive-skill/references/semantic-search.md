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

## Two installation paths

Pick one based on what you already have:

| Mode | When to pick | Speed (Apple Silicon) | Cleanup |
|---|---|---|---|
| **Native binary** (`install-semantic.sh`) | Default; no Docker on machine | **~20ms / embed call** (Metal accelerated) | rm -rf ~/claude-archive/ollama-bin |
| **Docker container** (`install-semantic-docker.sh`) | You already use Docker Desktop / want clean container | ~80ms / embed call (no Metal in Docker on Mac) | docker rm -f + docker volume rm |

For Linux + NVIDIA GPU: Docker mode supports `--gpus=all` (set `OLLAMA_GPU=all` before running the script).

### Path A — Native binary (recommended on macOS)

```bash
./scripts/install-semantic.sh
```

What it does:
1. Downloads ollama binary tarball from GitHub releases (~125 MB)
2. Extracts to `~/claude-archive/ollama-bin/`, symlinks to `~/bin/ollama`
3. Registers `ollama serve` with launchd → auto-start at login, restart on crash
4. Pulls `nomic-embed-text` model (~274 MB)
5. Creates `~/claude-archive/.venv` with `sqlite-vec` + `requests`
6. Copies `embed.py`, `vsearch.py`, `vsearch` wrapper
7. Kicks off backfill in background

### Path B — Docker container (cross-platform, easier cleanup)

```bash
./scripts/install-semantic-docker.sh
```

What it does:
1. Pulls `ollama/ollama` image (~1 GB)
2. Runs container `claude-archive-ollama` with `--restart unless-stopped`
3. Publishes port 11434 to localhost (same API endpoint, transparent to embed.py / vsearch.py)
4. Pulls `nomic-embed-text` inside container
5. Same venv + scripts setup as native path
6. Same backfill kick-off

Caveat for macOS: Docker uses a Linux VM, no Metal GPU passthrough → embedding ~3-5x slower than native. Backfill of 100k rows takes ~3-5 hours instead of ~1 hour. Functionally identical, just slower for the one-time backfill. Steady-state incremental embed (a few new rows per 15-min ingest tick) is unaffected.

### Manual install (no script)

If you want to do steps yourself, see the source of `install-semantic.sh` — the steps are commented and idempotent.

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

### Native install
```bash
USER=$(whoami)
launchctl unload ~/Library/LaunchAgents/com.${USER}.ollama.plist 2>/dev/null
rm -f ~/Library/LaunchAgents/com.${USER}.ollama.plist
pkill -f 'ollama serve'
rm -rf ~/.ollama ~/claude-archive/ollama-bin
rm -f ~/bin/ollama
```

### Docker install
```bash
docker rm -f claude-archive-ollama
docker volume rm ollama
rm -f ~/bin/ollama   # the docker exec wrapper
```

### Common (both modes)
```bash
# Drop vec table (preserves msg / FTS5)
sqlite3 ~/claude-archive/sessions.db "DROP TABLE msg_vec"

# Remove vsearch
rm -f ~/bin/vsearch ~/claude-archive/embed.py ~/claude-archive/vsearch.py
```

`csearch` and the rest of the base skill keep working unchanged. `build.py`'s `maybe_embed_new()` is a silent no-op if `embed.py` / Ollama is missing, so removal is safe.

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
