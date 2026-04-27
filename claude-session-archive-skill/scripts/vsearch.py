#!/usr/bin/env python3
"""
vsearch — semantic search over Claude session archive via Ollama + sqlite-vec.

Usage:
  vsearch '<natural language query>' [project-suffix]

Pipeline:
  1. Embed query via Ollama (nomic-embed-text)
  2. KNN top-200 over msg_vec
  3. Optionally filter by project, take top 20
  4. Display ranked by cosine distance (lower = more similar)

Complement to csearch (FTS5 lexical):
  - csearch  — exact phrase / boolean / prefix; fast, lexical
  - vsearch  — concept / synonym / cross-language; semantic
"""
import sqlite3
import sys
from pathlib import Path

# Make embed.py importable when this script is symlinked or invoked from elsewhere
sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed import (
    DB_PATH,
    embed_text,
    ensure_vec_schema,
    vec_to_blob,
)


def main():
    if len(sys.argv) < 2:
        print("usage: vsearch '<query>' [project-suffix]", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]
    proj = sys.argv[2] if len(sys.argv) >= 3 else None

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA mmap_size=536870912")
    conn.execute("PRAGMA cache_size=-524288")
    ensure_vec_schema(conn)

    qemb = embed_text(query)
    if qemb is None:
        print("ERROR: empty query or Ollama not running (curl localhost:11434)", file=sys.stderr)
        sys.exit(2)

    qblob = vec_to_blob(qemb)

    # KNN top-200, filter by project after, return top 20
    sql = """
        WITH knn AS (
            SELECT rowid, distance
            FROM msg_vec
            WHERE embedding MATCH ? AND k = 200
            ORDER BY distance
        )
        SELECT substr(m.session_id, 1, 8) AS session,
               substr(m.ts, 1, 19) AS ts,
               COALESCE(m.tool_name, '-') AS tool,
               printf('%.3f', knn.distance) AS sim,
               substr(replace(m.content, X'0A', ' '), 1, 180) AS snippet
        FROM knn JOIN msg m ON m.rowid = knn.rowid
        WHERE 1=1
    """
    params = [qblob]
    if proj:
        sql += " AND m.project LIKE ?"
        params.append(f"%{proj}%")

    sql += " ORDER BY knn.distance LIMIT 20"

    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()

    if not rows:
        print("no hits", file=sys.stderr)
        sys.exit(0)

    headers = ["session", "ts", "tool", "sim", "snippet"]
    widths = [8, 19, 10, 5, 80]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        truncated = [str(c)[:w] for c, w in zip(row, widths)]
        print(fmt.format(*truncated))


if __name__ == "__main__":
    main()
