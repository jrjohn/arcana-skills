#!/usr/bin/env python3
"""
csearch — FTS5 lexical search over Claude session archive.

Usage:
  csearch '<fts5-query>' [project-suffix]

Examples:
  csearch ZyXEL
  csearch '"port auto-power-down"'         # exact phrase
  csearch 'Sophos AND SEDService' network  # boolean + project filter
  csearch 'somnic*'                        # prefix

Complement to vsearch (semantic):
  - csearch  — exact phrase / boolean / prefix; fast, lexical
  - vsearch  — concept / synonym / cross-language; semantic
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path.home() / "claude-archive" / "sessions.db"


def main():
    if len(sys.argv) < 2:
        print("usage: csearch '<fts5-query>' [project-suffix]", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]
    proj = sys.argv[2] if len(sys.argv) >= 3 else None

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA mmap_size=536870912")
    conn.execute("PRAGMA cache_size=-524288")

    sql = """
        SELECT substr(m.session_id, 1, 8) AS session,
               substr(m.ts, 1, 19) AS ts,
               COALESCE(m.role, '-') AS role,
               COALESCE(m.tool_name, '-') AS tool,
               substr(replace(m.content, X'0A', ' '), 1, 180) AS snippet
        FROM msg m
        WHERE m.rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH ?)
    """
    params = [query]
    if proj:
        sql += " AND m.project LIKE ?"
        params.append(f"%{proj}%")
    sql += " ORDER BY m.ts DESC LIMIT 30"

    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
    except sqlite3.OperationalError as e:
        print(f"FTS5 syntax error: {e}", file=sys.stderr)
        print("tips: phrases use double-quotes; AND/OR/NOT must be UPPERCASE; prefix uses *", file=sys.stderr)
        sys.exit(2)

    if not rows:
        print("no hits", file=sys.stderr)
        sys.exit(0)

    headers = ["session", "ts", "role", "tool", "snippet"]
    widths = [8, 19, 9, 10, 80]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        truncated = [str(c)[:w] for c, w in zip(row, widths)]
        print(fmt.format(*truncated))


if __name__ == "__main__":
    main()
