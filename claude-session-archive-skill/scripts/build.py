#!/usr/bin/env python3
"""
Build SQLite FTS5 index over Claude Code session JSONL files.

Source: ~/.claude/projects/-*/*.jsonl
Target: ~/claude-archive/sessions.db

Schema:
  msg(session_id, project, seq, ts, role, tool_name, content)
  msg_fts (virtual FTS5 over content)

Idempotent: uses (session_id, seq) PK with INSERT OR REPLACE.
"""
import json
import os
import sqlite3
import sys
from glob import glob
from pathlib import Path

HOME = Path.home()
SRC_GLOB = str(HOME / '.claude' / 'projects' / '*' / '*.jsonl')
DB_DIR = HOME / 'claude-archive'
DB_PATH = DB_DIR / 'sessions.db'


def ensure_schema(conn):
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS msg (
            session_id TEXT NOT NULL,
            project    TEXT NOT NULL,
            seq        INTEGER NOT NULL,
            ts         TEXT,
            role       TEXT,
            tool_name  TEXT,
            content    TEXT,
            PRIMARY KEY (session_id, seq)
        );
        CREATE INDEX IF NOT EXISTS idx_msg_ts      ON msg(ts);
        CREATE INDEX IF NOT EXISTS idx_msg_project ON msg(project, ts);
        CREATE INDEX IF NOT EXISTS idx_msg_tool    ON msg(tool_name);

        CREATE VIRTUAL TABLE IF NOT EXISTS msg_fts USING fts5(
            content,
            content='msg', content_rowid='rowid',
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE TRIGGER IF NOT EXISTS msg_ai AFTER INSERT ON msg BEGIN
            INSERT INTO msg_fts(rowid, content) VALUES (new.rowid, new.content);
        END;
        CREATE TRIGGER IF NOT EXISTS msg_ad AFTER DELETE ON msg BEGIN
            INSERT INTO msg_fts(msg_fts, rowid, content) VALUES('delete', old.rowid, old.content);
        END;
        CREATE TRIGGER IF NOT EXISTS msg_au AFTER UPDATE ON msg BEGIN
            INSERT INTO msg_fts(msg_fts, rowid, content) VALUES('delete', old.rowid, old.content);
            INSERT INTO msg_fts(rowid, content) VALUES (new.rowid, new.content);
        END;

        CREATE TABLE IF NOT EXISTS ingest_state (
            file_path TEXT PRIMARY KEY,
            mtime     REAL,
            lines     INTEGER
        );
    """)
    conn.commit()


def flatten_content(msg):
    """Extract text from a Claude Code message. Returns (role, tool_name, text)."""
    role = msg.get('role') or msg.get('type') or 'unknown'
    content = msg.get('content') or msg.get('message', {}).get('content')
    if isinstance(content, str):
        return role, None, content
    if not isinstance(content, list):
        return role, None, json.dumps(msg, ensure_ascii=False)[:8000]

    parts = []
    tool_name = None
    for block in content:
        if not isinstance(block, dict):
            parts.append(str(block))
            continue
        btype = block.get('type')
        if btype == 'text':
            parts.append(block.get('text', ''))
        elif btype == 'tool_use':
            tool_name = block.get('name')
            parts.append(f"[TOOL_USE {tool_name}] input={json.dumps(block.get('input',{}), ensure_ascii=False)[:4000]}")
        elif btype == 'tool_result':
            c = block.get('content', '')
            if isinstance(c, list):
                for cc in c:
                    if isinstance(cc, dict) and cc.get('type') == 'text':
                        parts.append(cc.get('text', ''))
                    else:
                        parts.append(json.dumps(cc, ensure_ascii=False)[:4000])
            else:
                parts.append(str(c))
            parts.insert(0, "[TOOL_RESULT] ")
        elif btype == 'thinking':
            parts.append(f"[THINKING] {block.get('thinking','')}")
        else:
            parts.append(json.dumps(block, ensure_ascii=False)[:4000])
    return role, tool_name, '\n'.join(parts)


def ingest_file(conn, path):
    session_id = Path(path).stem
    project = Path(path).parent.name  # e.g. -Users-jrjohn-Documents-projects-network
    mtime = os.path.getmtime(path)

    cur = conn.cursor()
    row = cur.execute("SELECT mtime, lines FROM ingest_state WHERE file_path=?", (path,)).fetchone()
    prev_mtime, prev_lines = (row or (None, 0))
    if prev_mtime == mtime:
        return 0

    new_rows = 0
    with open(path, 'rb') as f:
        for seq, raw in enumerate(f):
            try:
                rec = json.loads(raw)
            except Exception:
                continue
            ts = rec.get('timestamp') or rec.get('ts') or ''
            role, tool_name, content = flatten_content(rec)
            content = (content or '').strip()
            if not content:
                continue
            cur.execute("""
                INSERT OR REPLACE INTO msg(session_id,project,seq,ts,role,tool_name,content)
                VALUES(?,?,?,?,?,?,?)
            """, (session_id, project, seq, ts, role, tool_name, content[:200000]))
            new_rows += 1

    cur.execute("INSERT OR REPLACE INTO ingest_state(file_path,mtime,lines) VALUES(?,?,?)",
                (path, mtime, new_rows))
    conn.commit()
    return new_rows


def maybe_embed_new(conn):
    """If embed.py is importable and Ollama is reachable, embed any new rows.
    Silent no-op otherwise — keeps build.py functional even without semantic stack."""
    try:
        import embed
    except ImportError:
        return
    try:
        embed.ensure_vec_schema(conn)
        # quick health check — don't burn time if ollama is down
        import requests
        requests.get("http://localhost:11434/api/tags", timeout=2)
    except Exception as e:
        print(f"(skip embedding: {e})")
        return
    embed.embed_missing(conn)


def refresh_recent_context():
    """For every known project (memory dir exists), regenerate auto_recent.md.
    Keeps long-running sessions seeing fresh context between SessionStart fires.

    Picks .ps1 (powershell.exe) on Windows, .sh elsewhere."""
    import subprocess, sys
    if sys.platform == 'win32':
        script = HOME / 'claude-archive' / 'gen-recent-context.ps1'
        cmd_prefix = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script)]
    else:
        script = HOME / 'claude-archive' / 'gen-recent-context.sh'
        cmd_prefix = [str(script)]
    if not script.exists():
        return
    proj_root = HOME / '.claude' / 'projects'
    if not proj_root.is_dir():
        return
    refreshed = 0
    for proj_dir in proj_root.glob('-*'):
        if (proj_dir / 'memory').is_dir():
            try:
                subprocess.run(
                    cmd_prefix,
                    env={**os.environ, 'CLAUDE_PROJECT_SLUG': proj_dir.name},
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=15,
                    check=False,
                )
                refreshed += 1
            except Exception:
                pass
    if refreshed:
        print(f"refreshed auto_recent.md for {refreshed} project(s)")


def main():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-524288")    # 512MB
    conn.execute("PRAGMA mmap_size=536870912")   # 512MB
    conn.execute("PRAGMA temp_store=MEMORY")
    ensure_schema(conn)

    files = sorted(glob(SRC_GLOB))
    total_new = 0
    touched = 0
    for f in files:
        n = ingest_file(conn, f)
        if n > 0:
            touched += 1
            total_new += n
            print(f"  +{n:6d}  {Path(f).parent.name}/{Path(f).name}")

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM msg")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT session_id) FROM msg")
    sess = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT project) FROM msg")
    proj = cur.fetchone()[0]

    print(f"\ntouched {touched} files, +{total_new} rows")
    print(f"DB total: {total} rows across {sess} sessions / {proj} projects")
    print(f"DB path:  {DB_PATH}")
    print(f"DB size:  {os.path.getsize(DB_PATH)/1024/1024:.1f} MB")

    # Optional: incremental semantic embedding (requires Ollama + sqlite-vec)
    maybe_embed_new(conn)

    conn.close()

    # Refresh auto_recent.md for all known projects (so long-running sessions get fresh context)
    refresh_recent_context()


if __name__ == '__main__':
    main()
