#!/usr/bin/env python3
"""
Embedding helpers for sessions.db using Ollama + sqlite-vec.

Provides:
- embed_text(text) -> list[float]                  (calls Ollama HTTP API)
- ensure_vec_schema(conn)                          (creates msg_vec virtual table)
- embed_missing(conn) -> int                       (backfill missing embeddings)

Used by:
- build.py main()           — runs incremental embed after ingest
- vsearch.py                — embeds query for KNN
- python embed.py (CLI)     — backfill standalone

Requires:
- Ollama running (http://localhost:11434) with `bge-m3` pulled
- Python venv with `sqlite-vec` and `requests` installed
"""
import os
import sqlite3
import struct
import sys
import time
from pathlib import Path

import requests
import sqlite_vec

# Model history:
#   v1.1.0 nomic-embed-text        768d  (137M, ~262MB) — English-only, weak on Chinese
#   v1.3.1 nomic-embed-text-v2-moe 768d  (305M MoE, ~957MB) — 100+ langs but Ollama hard-clamps
#                                  context to 512 tokens (Nomic confirms). Too short for our
#                                  session messages, abandoned.
#   v1.3.2 bge-m3                  1024d (568M, ~1.2GB) — multilingual SOTA on MIRACL, native
#                                  8192-token context, strong Chinese. dim change requires
#                                  msg_vec table rebuild.
EMBED_MODEL = "bge-m3"
EMBED_DIM = 1024
OLLAMA_URL = "http://localhost:11434/api/embeddings"
MAX_CHARS = 2000  # truncate long content; embedding captures gist not full text
DB_PATH = Path.home() / "claude-archive" / "sessions.db"


def embed_text(text):
    """Single Ollama embed call. Returns list[float] or None on empty/failure."""
    text = (text or "").strip()[:MAX_CHARS]
    if not text:
        return None
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=30,
        )
        r.raise_for_status()
        emb = r.json().get("embedding")
        if not emb or len(emb) != EMBED_DIM:
            return None
        return emb
    except Exception as e:
        print(f"embed error: {e}", file=sys.stderr)
        return None


def vec_to_blob(v):
    """Pack list[float] to bytes for vec0 storage (little-endian float32)."""
    return struct.pack(f"<{len(v)}f", *v)


def ensure_vec_schema(conn):
    """Load sqlite-vec extension and create msg_vec table if missing.
    Uses cosine distance (works for both normalized and unnormalized vectors)."""
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS msg_vec USING vec0(
            embedding float[{EMBED_DIM}] distance_metric=cosine
        )
    """)
    conn.commit()


def embed_missing(conn, batch_commit=200, progress_every=500):
    """Backfill embeddings for msg rows not yet in msg_vec.

    Returns number of rows newly embedded.
    Resumable: only processes rows missing from msg_vec.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT m.rowid, m.content
        FROM msg m
        LEFT JOIN msg_vec v ON v.rowid = m.rowid
        WHERE v.rowid IS NULL
        ORDER BY m.rowid
    """)
    rows = cur.fetchall()
    total = len(rows)
    if total == 0:
        print("nothing to embed (all msg rows already in msg_vec)")
        return 0

    print(f"embedding {total} rows via {EMBED_MODEL}...")
    done = 0
    skipped = 0
    started = time.time()

    for rowid, content in rows:
        emb = embed_text(content)
        if emb is None:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO msg_vec(rowid, embedding) VALUES (?, ?)",
            (rowid, vec_to_blob(emb)),
        )
        done += 1
        if done % batch_commit == 0:
            conn.commit()
        if done % progress_every == 0:
            elapsed = time.time() - started
            rate = done / elapsed
            eta_min = (total - done) / max(rate, 0.1) / 60
            print(f"  {done}/{total}  rate={rate:.1f}/s  eta={eta_min:.1f} min", flush=True)

    conn.commit()
    elapsed = time.time() - started
    print(f"embedded {done} rows in {elapsed/60:.1f} min  (skipped {skipped} empty)")
    return done


if __name__ == "__main__":
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-524288")
    conn.execute("PRAGMA mmap_size=536870912")
    conn.execute("PRAGMA temp_store=MEMORY")
    ensure_vec_schema(conn)
    embed_missing(conn)
    conn.close()
