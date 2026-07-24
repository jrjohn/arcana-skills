#!/usr/bin/env python3
"""
batch_create_conversations.py — Batch create official Antigravity Conversations for all active/recent Claude jobs
"""

import os
import sys
import json
import glob
import subprocess

CLAUDE_JOBS_DIR = os.path.expanduser("~/.claude/jobs")
AGENTAPI_BIN = os.path.expanduser("~/.gemini/antigravity/bin/agentapi")

def get_recent_jobs():
    pattern = os.path.join(CLAUDE_JOBS_DIR, "*", "state.json")
    state_files = glob.glob(pattern)
    jobs = []

    for s_file in state_files:
        try:
            with open(s_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            jobs.append(data)
        except Exception:
            pass

    jobs.sort(key=lambda x: x.get("updatedAt", ""), reverse=True)
    return jobs

def main():
    jobs = get_recent_jobs()
    
    # Priority jobs (Blocked / Needs Input first)
    priority_names = [
        "cloud project setup",
        "AI BPM developer",
        "Jobs",
        "token quota system",
        "GCP Cloude sda 硬碟縮小",
        "Software Architecture",
        "SomniLand Cloud",
        "charter memory review",
        "AI Session RAG deploy"
    ]

    created_count = 0
    for p_name in priority_names:
        matching_job = None
        for j in jobs:
            if p_name.lower() in j.get("name", "").lower():
                matching_job = j
                break

        if matching_job:
            name = matching_job.get("name", p_name)
            detail = matching_job.get("detail") or matching_job.get("needs") or ""
            cwd = matching_job.get("cwd", "")
            session_id = matching_job.get("sessionId", "")

            prompt = f"[Claude Task: {name}]\nSessionID: {session_id}\nCwd: {cwd}\nDetail: {detail}\n\n請協助接手並繼續執行此任務。"

            cmd = [
                AGENTAPI_BIN,
                "new-conversation",
                f"--title={name}",
                prompt
            ]

            print(f"Creating: [{name}]...")
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                created_count += 1
                print(f"  ✓ Created: {name}")
            else:
                print(f"  ❌ Error for {name}:", res.stderr)

    print(f"\n✓ Batch creation complete! Created {created_count} recent conversations.")

if __name__ == "__main__":
    main()
