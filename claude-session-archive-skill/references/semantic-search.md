# Semantic Search (Optional) — Ollama + sqlite-vec

The base skill ships with `csearch` (FTS5 lexical). For **concept-level / synonym / cross-language** queries, this optional add-on gives you `vsearch` backed by local embeddings.

## What you gain

| Need | csearch (FTS5) | vsearch (semantic) |
|---|---|---|
| Find exact phrase / IP / hostname | ✅ | weak |
| "上次討論 X 怎麼解的" without remembering keywords | ❌ | ✅ |
| 中英對照（`防火牆` 找到 `firewall`） | ❌ | ✅ |
| Concept query (`找權限管理相關決策`) | ❌ | ✅ |
| Speed | ~10 ms | ~150–300 ms (bge-m3) |
| Privacy | 100% local | 100% local (Ollama) |

`vsearch` complements, doesn't replace `csearch`. Use both.

## Embedding model: `bge-m3` (since v1.3)

| | bge-m3 |
|---|---|
| Size | 1.2 GB (568M params) |
| Dimensions | 1024 |
| Native context | **8192 tokens** (vs nomic 2048) |
| Multilingual | SOTA on MIRACL — **strong Chinese / 中文** |
| Latency | ~140 ms / call (warm, Apple Silicon Metal) |
| Storage | ~4 KB / row × 100k rows ≈ 400 MB |

**Model history** (in `embed.py` comments):
- **v1.1** nomic-embed-text (768d, 274 MB) — English-only, weak on Chinese
- **v1.3.1** nomic-embed-text-v2-moe (768d, 957 MB, 100+ langs) — abandoned: Ollama hard-clamps context to 512 tokens, too short for session messages
- **v1.3.2** **bge-m3 (1024d, 1.2 GB)** — current. Multilingual SOTA, native 8192 context, strong CJK

To switch model later: edit `EMBED_MODEL` + `EMBED_DIM` in `embed.py`, drop `msg_vec`, re-pull model, re-run `embed_parallel.py`.

## Architecture

```
~/.claude/projects/*/*.jsonl
       │
       ▼  build.py (ingest text + call embed_missing)
~/claude-archive/sessions.db
       ├── msg            FTS5 indexed (csearch)
       └── msg_vec        vec0 + bge-m3 (vsearch)
                          1024-dim, cosine distance
                                       │
                                       ▼
                          Ollama @ localhost:11434
                          (bge-m3, 1.2 GB, runs entirely locally)
                          OLLAMA_NUM_PARALLEL=4 for parallel backfill
```

## Two installation paths

Pick one based on what you already have:

| Mode | When to pick | Speed (Apple Silicon) | Cleanup |
|---|---|---|---|
| **Native binary** (`install-semantic.sh`) | Default; no Docker on machine | **~140ms / embed call** (Metal accelerated) | rm -rf ~/claude-archive/ollama-bin |
| **Docker container** (`install-semantic-docker.sh`) | You already use Docker Desktop / want clean container | ~500ms / embed call (no Metal in Docker on Mac) | docker rm -f + docker volume rm |

For Linux + NVIDIA GPU: Docker mode supports `--gpus=all` (set `OLLAMA_GPU=all` before running the script).

### Path A — Native binary (recommended on macOS)

```bash
./scripts/install-semantic.sh
```

What it does:
1. Downloads ollama binary tarball from GitHub releases (~125 MB)
2. Extracts to `~/claude-archive/ollama-bin/`, symlinks to `~/bin/ollama`
3. Registers `ollama serve` with launchd → auto-start at login, restart on crash
4. Pulls `bge-m3` model (~1.2 GB)
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
4. Pulls `bge-m3` inside container
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

Use both, default order:
1. `vsearch` first — most recall queries are paraphrased and benefit from semantic + cross-language match. ~50-150 ms with a warm Ollama daemon.
2. `csearch` as fallback — free, instant, but only fires on literal substrings. Go straight to `csearch` when the query *is* the exact literal you remember (IP, hostname, file path, error string, FTS5 boolean syntax). Also use `csearch` when `vsearch` returns nothing useful (rare; usually means the row hasn't been embedded yet).

## Schema additions

```sql
-- Created automatically by ensure_vec_schema()
CREATE VIRTUAL TABLE msg_vec USING vec0(
    embedding float[1024] distance_metric=cosine
);
-- rowid links to msg.rowid (1:1, sparse — only embedded rows present)
```

## Disk impact

- `bge-m3` model: 1.2 GB on disk (~/.ollama/models/)
- `msg_vec` table: ~4 KB / row (1024 floats × 4 bytes + overhead)
  - 100k rows ≈ 400 MB
  - 1M rows ≈ 4 GB

Compared to `msg` + FTS5 around 200 MB, the semantic stack adds another ~400 MB at current row count.

## Memory while running

- Ollama daemon: ~1.5 GB resident (bge-m3 loaded into Metal)
- Python query: ~100 MB during search (mmap dominates)
- Together: < 2 GB. On a 16GB+ Mac, irrelevant.

## Performance characteristics

| Component | Cold | Hot |
|---|---|---|
| Ollama bge-m3 embed (single) | 500-1500 ms | **140 ms** (Metal) |
| sqlite-vec KNN over 100k rows | ~30-80 ms (brute force) | same |
| msg JOIN | < 5 ms | < 5 ms |
| **Total `vsearch` end-to-end** | ~700 ms | **~150-300 ms** |

Ollama keeps the model resident for `OLLAMA_KEEP_ALIVE=30m` after last use. For frequent vsearch, calls stay warm.

## Parallel backfill (`embed_parallel.py`)

For initial backfill of 100k+ rows, sequential `embed.py` is slow (~7 emb/s single-thread = 4 hr). Use the parallel runner:

```bash
~/claude-archive/.venv/bin/python ~/claude-archive/embed_parallel.py 8
```

- Spawns 8 ThreadPoolExecutor workers, all calling Ollama HTTP concurrently
- Ollama batches them via `OLLAMA_NUM_PARALLEL=4` (set in launchd plist)
- Effective rate: ~7-10 emb/s (4-5x faster than sequential)
- Progress every 500 rows printed to stdout
- Resumable: only processes msg rows missing from msg_vec

`install-semantic.sh` / `.ps1` automatically runs `embed_parallel.py 8` for initial backfill.

After backfill, `build.py`'s `maybe_embed_new()` hook handles incremental new rows (small batches, sequential is fine).

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

## Why bge-m3?

- **1024-dim** — richer semantic space than 768-dim
- **Native 8192-token context** — full session messages fit, no truncation surprises
- **Multilingual SOTA** on MIRACL benchmark — strong Chinese / 中文 / Japanese / multilingual
- **1.2 GB** model on disk — bigger than nomic but still small enough for local inference
- Free, 100% local

Alternatives if you want to swap:
- `nomic-embed-text` — 768-dim, 274 MB, faster (~20 ms) but English-only, weak on Chinese
- `mxbai-embed-large` — 1024-dim, English-only, ~700 MB
- OpenAI `text-embedding-3-small` — but DB content goes to OpenAI = privacy violation

Edit `EMBED_MODEL` and `EMBED_DIM` in `embed.py` to change. After change:
1. Drop `msg_vec` table (different model = different vector space, can't mix)
2. Re-pull new model: `ollama pull <model>`
3. Re-run `embed_parallel.py 8` to backfill
