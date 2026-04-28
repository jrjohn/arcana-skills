#!/usr/bin/env python3
"""
Parallel re-embed runner — uses ThreadPoolExecutor to fan out Ollama HTTP calls.
Resumable: only processes msg rows not yet in msg_vec.

Usage:
    embed_parallel.py [num_workers]    # default 4

embed.py's sequential embed_missing() drives Ollama at ~5.8 emb/sec on bge-m3
(single-threaded HTTP). With 4 parallel workers Ollama can queue/batch them
internally and we typically see 3–5× throughput.
"""
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import os, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from embed import (
    DB_PATH,
    EMBED_MODEL,
    embed_text,
    ensure_vec_schema,
    vec_to_blob,
)


def main():
    num_workers = int(sys.argv[1]) if len(sys.argv) >= 2 else 4

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-524288")
    conn.execute("PRAGMA mmap_size=536870912")
    conn.execute("PRAGMA temp_store=MEMORY")
    ensure_vec_schema(conn)

    cur = conn.cursor()
    cur.execute(
        """
        SELECT m.rowid, m.content
        FROM msg m LEFT JOIN msg_vec v ON v.rowid = m.rowid
        WHERE v.rowid IS NULL
        ORDER BY m.rowid
    """
    )
    rows = cur.fetchall()
    total = len(rows)
    if total == 0:
        print("nothing to embed (all msg rows already in msg_vec)")
        return

    print(f"embedding {total} rows via {EMBED_MODEL} with {num_workers} workers ...")

    done = 0
    skipped = 0
    started = time.time()

    def embed_one(rowid, content):
        return rowid, embed_text(content)

    # Stream submission so 100k futures don't all land in memory at once.
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        in_flight = {}
        row_iter = iter(rows)
        # Prime the pipe
        for _ in range(num_workers * 8):
            try:
                rowid, content = next(row_iter)
            except StopIteration:
                break
            in_flight[executor.submit(embed_one, rowid, content)] = rowid

        while in_flight:
            for future in as_completed(list(in_flight.keys())):
                in_flight.pop(future, None)
                rowid, emb = future.result()
                if emb is None:
                    skipped += 1
                else:
                    conn.execute(
                        "INSERT INTO msg_vec(rowid, embedding) VALUES (?, ?)",
                        (rowid, vec_to_blob(emb)),
                    )
                    done += 1
                    if done % 200 == 0:
                        conn.commit()
                    if done % 500 == 0:
                        elapsed = time.time() - started
                        rate = done / elapsed
                        eta_min = (total - done) / max(rate, 0.1) / 60
                        print(
                            f"  {done}/{total}  rate={rate:.1f}/s  eta={eta_min:.1f} min",
                            flush=True,
                        )

                # Refill pipe
                try:
                    rowid_next, content_next = next(row_iter)
                    in_flight[executor.submit(embed_one, rowid_next, content_next)] = rowid_next
                except StopIteration:
                    pass

                # Re-poll (loop back to as_completed with fresh keys)
                break

    conn.commit()
    elapsed = time.time() - started
    print(
        f"embedded {done} rows in {elapsed/60:.1f} min  (skipped {skipped} empty, "
        f"{num_workers} workers)"
    )


if __name__ == "__main__":
    main()
