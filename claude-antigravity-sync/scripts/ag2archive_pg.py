#!/usr/bin/env python3
"""
ag2archive_pg.py — Ingest Antigravity session transcripts into shared PostgreSQL (archive_main)
Uses environment variables from ~/.config/crs/env.sh
"""

import os
import glob
import json
import time
import urllib.request
import psycopg2
from psycopg2.extras import execute_values

OLLAMA_URL = "http://localhost:11434/api/embeddings"
BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity/brain")
INGEST_STATE_FILE = os.path.expanduser("~/antigravity-archive/pg_ingest_state.json")

def get_pg_connection():
    # Source env from ~/.config/crs/env.sh if needed
    env_sh = os.path.expanduser("~/.config/crs/env.sh")
    if os.path.exists(env_sh):
        import subprocess
        command = f"source {env_sh} && env"
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        for line in proc.stdout:
            (key, _, value) = line.decode().partition("=")
            os.environ[key.strip()] = value.strip()

    host = os.environ.get("CRS_PG_HOST", "arcana.boo")
    port = os.environ.get("CRS_PG_PORT", 5432)
    user = os.environ.get("CRS_PG_USER", "archive")
    password = os.environ.get("CRS_PG_PASSWORD", "")
    dbname = os.environ.get("CRS_PG_DB", "archive_main")

    return psycopg2.connect(
        host=host, port=port, user=user, password=password, dbname=dbname
    )

def get_embedding(text):
    """Fetch 1024-dim embedding from Ollama bge-m3 model."""
    if not text or len(text.strip()) == 0:
        return None
    try:
        truncated_text = text[:2000]
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps({"model": "bge-m3", "prompt": truncated_text}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read())
            vec = data.get("embedding", [])
            if vec and len(vec) == 1024:
                return vec
    except Exception:
        pass
    return None

def load_ingest_state():
    if os.path.exists(INGEST_STATE_FILE):
        try:
            with open(INGEST_STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_ingest_state(state):
    os.makedirs(os.path.dirname(INGEST_STATE_FILE), exist_ok=True)
    with open(INGEST_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def parse_transcript_line(line_str, seq_counter):
    try:
        data = json.loads(line_str)
    except Exception:
        return None, seq_counter

    source = data.get("source", "")
    step_type = data.get("type", "")
    content = data.get("content", "")
    tool_calls = data.get("tool_calls", [])
    
    if source == "USER_EXPLICIT" or step_type == "USER_INPUT":
        role = "user"
    elif source == "MODEL" or step_type == "PLANNER_RESPONSE":
        role = "assistant"
    else:
        role = "system"

    records = []
    
    if content:
        if isinstance(content, (dict, list)):
            text_str = json.dumps(content, ensure_ascii=False)
        else:
            text_str = str(content)
        if text_str.strip():
            records.append({
                "seq": seq_counter,
                "role": role,
                "tool_name": None,
                "content": text_str
            })
            seq_counter += 1

    for tc in tool_calls:
        if isinstance(tc, dict):
            t_name = tc.get("name") or tc.get("tool_name") or "tool"
            t_args = tc.get("args") or tc.get("parameters") or {}
            t_str = f"Tool Call [{t_name}]: {json.dumps(t_args, ensure_ascii=False)}"
            records.append({
                "seq": seq_counter,
                "role": "tool",
                "tool_name": t_name,
                "content": t_str
            })
            seq_counter += 1

    return records, seq_counter

def process_file(conn, file_path, state):
    mtime = os.path.getmtime(file_path)
    file_info = state.get(file_path, {})
    
    if file_info.get("mtime") == mtime:
        return 0

    prev_lines = file_info.get("lines", 0)

    parts = file_path.split(os.sep)
    conv_id = "unknown"
    if "brain" in parts:
        b_idx = parts.index("brain")
        if b_idx + 1 < len(parts):
            conv_id = parts[b_idx + 1]

    project = f"antigravity:{conv_id[:8]}"
    session_id = f"ag-{conv_id}"

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    total_lines = len(all_lines)
    if total_lines <= prev_lines and file_info:
        return 0

    cur = conn.cursor()
    cur.execute("SELECT MAX(seq) FROM msg WHERE session_id = %s", (session_id,))
    max_seq_row = cur.fetchone()
    seq_counter = (max_seq_row[0] + 1) if (max_seq_row and max_seq_row[0] is not None) else 0

    inserted_count = 0
    now_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for idx, line in enumerate(all_lines[prev_lines:], start=prev_lines):
        line = line.strip()
        if not line:
            continue
        parsed_records, seq_counter = parse_transcript_line(line, seq_counter)
        if not parsed_records:
            continue

        for rec in parsed_records:
            emb_vec = get_embedding(rec["content"])
            emb_str = f"[{','.join(map(str, emb_vec))}]" if emb_vec else None
            
            cur.execute("""
                INSERT INTO msg (session_id, project, seq, ts, role, tool_name, content, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (session_id, seq) DO UPDATE
                SET ts = EXCLUDED.ts, role = EXCLUDED.role, tool_name = EXCLUDED.tool_name,
                    content = EXCLUDED.content, embedding = EXCLUDED.embedding
            """, (session_id, project, rec["seq"], now_ts, rec["role"], rec["tool_name"], rec["content"], emb_str))
            conn.commit()
            inserted_count += 1

    conn.commit()
    state[file_path] = {"mtime": mtime, "lines": total_lines}
    return inserted_count

def main():
    try:
        conn = get_pg_connection()
    except Exception as e:
        print(f"[ag2archive_pg] Failed to connect to PostgreSQL: {e}")
        return

    state = load_ingest_state()
    pattern = os.path.join(BRAIN_DIR, "*", ".system_generated", "logs", "transcript.jsonl")
    transcript_files = glob.glob(pattern)

    total_inserted = 0
    for fpath in transcript_files:
        try:
            count = process_file(conn, fpath, state)
            total_inserted += count
        except Exception as e:
            print(f"[ag2archive_pg] Error processing {fpath}: {e}")

    conn.close()
    save_ingest_state(state)
    print(f"[ag2archive_pg] Successfully synced {total_inserted} records into PostgreSQL (archive_main at arcana.boo)")

if __name__ == "__main__":
    main()
