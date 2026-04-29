#!/usr/bin/env python3
"""
vsearch-since — semantic search over recent (time-bounded) Claude session archive.

Like vsearch, but:
- filters by project (substring match) AND ts >= now - hours
- emits markdown bullets (one line per hit) instead of a table
- de-noises with min/max content length

Usage:
  vsearch-since.py --query '<text>' --project '<slug-substr>' \
                   --hours 48 --limit 10 [--min-len 30] [--max-len 600]

Designed for SessionStart hooks: surfaces the messages from the last N hours
that are most semantically related to a "current focus" query (e.g. pending list).
"""
import argparse
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed import DB_PATH, embed_text, ensure_vec_schema, vec_to_blob


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="natural-language query text")
    ap.add_argument("--project", required=True, help="project slug substring")
    ap.add_argument("--hours", type=int, default=48)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--min-len", type=int, default=30)
    ap.add_argument("--max-len", type=int, default=600)
    ap.add_argument("--max-distance", type=float, default=0.65,
                    help="cosine distance cutoff (bge-m3: <0.4 strong, 0.4-0.6 related, >0.7 noise)")
    ap.add_argument("--max-snippet", type=int, default=180,
                    help="max chars per snippet in output (lower → fewer tokens when Claude reads)")
    ap.add_argument("--knn", type=int, default=400, help="KNN pool before time/project filter")
    args = ap.parse_args()

    qemb = embed_text(args.query)
    if qemb is None:
        print("ERROR: empty query or Ollama not running", file=sys.stderr)
        sys.exit(2)

    since_ts = (datetime.now() - timedelta(hours=args.hours)).strftime("%Y-%m-%dT%H:%M:%S")

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA mmap_size=536870912")
    ensure_vec_schema(conn)

    sql = """
        WITH knn AS (
            SELECT rowid, distance
            FROM msg_vec
            WHERE embedding MATCH ? AND k = ?
            ORDER BY distance
        )
        SELECT substr(m.ts, 1, 16) AS ts,
               m.role AS role,
               COALESCE(m.tool_name, '-') AS tool,
               printf('%.3f', knn.distance) AS sim,
               replace(replace(m.content, X'0A', ' '), X'09', ' ') AS content
        FROM knn JOIN msg m ON m.rowid = knn.rowid
        WHERE m.project LIKE ?
          AND m.ts >= ?
          AND knn.distance <= ?
          AND length(m.content) BETWEEN ? AND ?
          AND m.content NOT LIKE '[TOOL_RESULT]%'
          AND m.content NOT LIKE '[TOOL_USE%'
          AND m.content NOT LIKE '[THINKING%'
          AND m.content NOT LIKE '<%'
        ORDER BY knn.distance
        LIMIT ?
    """
    cur = conn.cursor()
    cur.execute(sql, (
        vec_to_blob(qemb),
        args.knn,
        f"%{args.project}%",
        since_ts,
        args.max_distance,
        args.min_len,
        args.max_len,
        args.limit,
    ))
    rows = cur.fetchall()

    if not rows:
        print("_(vsearch-since: no hits in last %dh)_" % args.hours)
        return

    cap = args.max_snippet
    for ts, role, tool, sim, content in rows:
        snippet = content.strip()
        if len(snippet) > cap:
            snippet = snippet[:cap - 3] + "..."
        tag = role if tool == "-" else f"{role}/{tool}"
        print(f"- **{ts}** `{tag}` (sim={sim}) — {snippet}")


if __name__ == "__main__":
    main()
