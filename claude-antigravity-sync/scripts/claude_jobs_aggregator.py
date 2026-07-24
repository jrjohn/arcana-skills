#!/usr/bin/env python3
"""
claude_jobs_aggregator.py — Aggregate Claude Code Agent Tasks and Antigravity Conversations
"""

import os
import glob
import json
from datetime import datetime, timezone

CLAUDE_JOBS_DIR = os.path.expanduser("~/.claude/jobs")
AG_BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity/brain")

def parse_claude_jobs():
    pattern = os.path.join(CLAUDE_JOBS_DIR, "*", "state.json")
    state_files = glob.glob(pattern)

    needs_input = []
    working = []
    completed = []

    for s_file in state_files:
        try:
            with open(s_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            
            name = data.get("name") or os.path.basename(os.path.dirname(s_file))
            state = data.get("state", "unknown")
            tempo = data.get("tempo", "")
            detail = data.get("detail") or data.get("needs") or ""
            updated_at = data.get("updatedAt") or data.get("createdAt") or ""
            session_id = data.get("sessionId", "")

            # Calculate relative time string
            age_str = ""
            if updated_at:
                try:
                    dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    delta = now - dt
                    if delta.days > 0:
                        age_str = f"{delta.days}d"
                    elif delta.seconds >= 3600:
                        age_str = f"{delta.seconds // 3600}h"
                    elif delta.seconds >= 60:
                        age_str = f"{delta.seconds // 60}m"
                    else:
                        age_str = f"{delta.seconds}s"
                except Exception:
                    pass

            item = {
                "name": name,
                "detail": detail,
                "state": state,
                "updated_at": updated_at,
                "age": age_str,
                "session_id": session_id
            }

            if state in ("blocked", "needs_input", "paused") or "wait" in detail.lower() or "limit" in detail.lower():
                needs_input.append(item)
            elif state in ("running", "working", "in_flight"):
                working.append(item)
            else:
                completed.append(item)

        except Exception as e:
            pass

    # Sort each list by updated_at descending
    needs_input.sort(key=lambda x: x["updated_at"], reverse=True)
    working.sort(key=lambda x: x["updated_at"], reverse=True)
    completed.sort(key=lambda x: x["updated_at"], reverse=True)

    return needs_input, working, completed

def parse_antigravity_conversations():
    pattern = os.path.join(AG_BRAIN_DIR, "*", ".system_generated", "logs", "transcript.jsonl")
    transcript_files = glob.glob(pattern)

    ag_convs = []
    for t_file in transcript_files:
        try:
            mtime = os.path.getmtime(t_file)
            parts = t_file.split(os.sep)
            conv_id = parts[parts.index("brain") + 1] if "brain" in parts else "unknown"

            # Read first user input or prompt
            first_prompt = ""
            last_prompt = ""
            with open(t_file, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        if obj.get("source") == "USER_EXPLICIT" or obj.get("type") == "USER_INPUT":
                            cnt = str(obj.get("content", "")).strip()
                            if cnt:
                                if not first_prompt:
                                    first_prompt = cnt
                                last_prompt = cnt
                    except Exception:
                        pass

            title = first_prompt.replace("\n", " ")[:60] if first_prompt else f"Conversation {conv_id[:8]}"
            dt = datetime.fromtimestamp(mtime, timezone.utc)
            now = datetime.now(timezone.utc)
            delta = now - dt
            age_str = f"{delta.days}d" if delta.days > 0 else (f"{delta.seconds // 3600}h" if delta.seconds >= 3600 else f"{delta.seconds // 60}m")

            ag_convs.append({
                "conv_id": conv_id,
                "title": title,
                "last_prompt": last_prompt.replace("\n", " ")[:80],
                "mtime": mtime,
                "age": age_str
            })
        except Exception:
            pass

    ag_convs.sort(key=lambda x: x["mtime"], reverse=True)
    return ag_convs

def generate_markdown_report():
    needs_input, working, completed = parse_claude_jobs()
    ag_convs = parse_antigravity_conversations()

    lines = []
    lines.append("# Conversations & Claude Code Agent Tasks Overview\n")
    lines.append(f"*Updated at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*\n")

    lines.append("##  Needs Input / Blocked Tasks (Claude Code)")
    if needs_input:
        for item in needs_input:
            det = f" — `{item['detail'][:80]}`" if item['detail'] else ""
            lines.append(f"- **{item['name']}** ({item['age']}){det}")
    else:
        lines.append("- *None*")
    lines.append("")

    lines.append("## ⚡ Working Tasks (Claude Code)")
    if working:
        for item in working:
            det = f" — `{item['detail'][:80]}`" if item['detail'] else ""
            lines.append(f"- **{item['name']}** ({item['age']}){det}")
    else:
        lines.append("- *None*")
    lines.append("")

    lines.append("##  Completed Agent Tasks (Claude Code)")
    if completed:
        for item in completed:
            det = f" — `{item['detail'][:80]}`" if item['detail'] else ""
            lines.append(f"- **{item['name']}** ({item['age']}){det}")
    else:
        lines.append("- *None*")
    lines.append("")

    lines.append("## 🤖 Antigravity Conversations")
    if ag_convs:
        for conv in ag_convs:
            lines.append(f"- **[{conv['conv_id'][:8]}]** `{conv['title']}` ({conv['age']})")
    else:
        lines.append("- *None*")

    return "\n".join(lines)

if __name__ == "__main__":
    report = generate_markdown_report()
    print(report)
    target_path = os.path.expanduser("~/.gemini/antigravity/scratch/CLAUDE_JOBS.md")
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(report)
    except Exception:
        pass
