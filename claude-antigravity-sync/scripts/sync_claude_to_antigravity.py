#!/usr/bin/env python3
"""
sync_claude_to_antigravity.py — Sync Claude Code jobs into Antigravity Brain transcripts
and keep both Antigravity Conversations & Claude Code tasks synchronized in PostgreSQL.
"""

import os
import glob
import json
import time
from datetime import datetime, timezone

CLAUDE_JOBS_DIR = os.path.expanduser("~/.claude/jobs")
AG_BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity/brain")

def sync_job_to_ag_brain(job_dir):
    state_file = os.path.join(job_dir, "state.json")
    if not os.path.exists(state_file):
        return None

    try:
        with open(state_file, "r", encoding="utf-8", errors="replace") as f:
            state_data = json.load(f)
    except Exception:
        return None

    job_id = state_data.get("sessionId") or os.path.basename(job_dir)
    job_name = state_data.get("name") or job_id
    detail = state_data.get("detail") or state_data.get("needs") or ""
    status = state_data.get("state", "unknown")
    cwd = state_data.get("cwd", "")
    updated_at = state_data.get("updatedAt", "")

    # Target brain directory for this Claude job
    ag_conv_id = f"claude-{job_id[:24]}"
    ag_brain_path = os.path.join(AG_BRAIN_DIR, ag_conv_id)
    logs_dir = os.path.join(ag_brain_path, ".system_generated", "logs")
    os.makedirs(logs_dir, exist_ok=True)

    transcript_file = os.path.join(logs_dir, "transcript.jsonl")

    # Read timeline or linkScanPath if exists
    timeline_file = os.path.join(job_dir, "timeline.jsonl")
    link_path = state_data.get("linkScanPath", "")

    events = []
    
    # Event 1: Job metadata header
    events.append({
        "step_index": 0,
        "source": "USER_EXPLICIT",
        "type": "USER_INPUT",
        "status": "DONE",
        "content": f"[Claude Task: {job_name}] Cwd: {cwd} | Status: {status}"
    })

    if detail:
        events.append({
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "content": f"Status detail: {detail}"
        })

    # Read timeline lines if present
    if os.path.exists(timeline_file):
        try:
            with open(timeline_file, "r", encoding="utf-8", errors="replace") as f:
                for idx, line in enumerate(f, start=2):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        t_obj = json.loads(line)
                        t_type = t_obj.get("type", "")
                        t_text = t_obj.get("text") or t_obj.get("content") or t_obj.get("message") or ""
                        if t_text:
                            events.append({
                                "step_index": idx,
                                "source": "MODEL" if "assistant" in t_type else "USER_EXPLICIT",
                                "type": "PLANNER_RESPONSE" if "assistant" in t_type else "USER_INPUT",
                                "status": "DONE",
                                "content": str(t_text)
                            })
                    except Exception:
                        pass
        except Exception:
            pass

    # Write transcript.jsonl
    with open(transcript_file, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    return ag_conv_id

def main():
    if not os.path.exists(CLAUDE_JOBS_DIR):
        print(f"Claude jobs directory {CLAUDE_JOBS_DIR} not found.")
        return

    job_dirs = [os.path.join(CLAUDE_JOBS_DIR, d) for d in os.listdir(CLAUDE_JOBS_DIR) if os.path.isdir(os.path.join(CLAUDE_JOBS_DIR, d))]

    synced_count = 0
    for j_dir in job_dirs:
        conv_id = sync_job_to_ag_brain(j_dir)
        if conv_id:
            synced_count += 1

    print(f"[sync_claude_to_antigravity] Synced {synced_count} Claude agent jobs into Antigravity Brain transcripts.")

if __name__ == "__main__":
    main()
