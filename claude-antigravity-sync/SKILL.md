---
name: claude-antigravity-sync
description: Synchronizes Claude Code Agent Jobs into Antigravity conversations, PostgreSQL RAG archive, and manages CLI bridge tools (agjobs, agload).
---

# Claude Code Trajectory Sync Skill

This skill governs the synchronization, recall, and management of **Claude Code Agent Jobs (`~/.claude/jobs/`)** inside **Antigravity**.

## Architecture Overview

```
[Claude Code Jobs] ~/.claude/jobs/*/state.json
       │
       ├── 1. Transcripts Sync ──► ~/.gemini/antigravity/brain/claude-*/.system_generated/logs/transcript.jsonl
       │
       ├── 2. Native Conversations ──► agentapi new-conversation (Registers in state.vscdb & Conversations sidebar)
       │
       └── 3. Vector & RAG Archive ──► PostgreSQL archive_main@arcana.boo (bge-m3 1024-dim embeddings)
```

- **Trajectory Sync Direction**: One-way (`Claude Code -> Antigravity`) to preserve Claude's daemon state locks, avoid schema mismatch, and prevent echo loops.
- **RAG Knowledge Search**: Bi-directional (`Antigravity ↔ Claude Code`) via shared PostgreSQL `archive_main@arcana.boo` using `agsearch` / `osearch`.

---

## Command & Tool Reference

| Tool / CLI | Path | Description |
|---|---|---|
| `agjobs` | `/Users/jrjohn/bin/agjobs` | Displays live overview of Needs Input, Working, and Completed Claude agent tasks. |
| `agload` | `/Users/jrjohn/bin/agload` | Loads and resumes context of any Claude Code job by name or session ID. |
| `agentapi` | `/Users/jrjohn/.gemini/antigravity/bin/agentapi` | Official Antigravity CLI to create native conversations. |
| `sync_all.sh` | `/Users/jrjohn/antigravity-archive/sync_all.sh` | Master sync script executed every 15 mins by launchd (`com.jrjohn.antigravity-archive.plist`). |

---

## Agent Instructions & Rules

1. **When User asks to load or continue a job** (e.g., `"載入 Somnics Cloud 統計"`, `"繼續 MIS"`):
   - Execute `/Users/jrjohn/bin/agload "<job_name>"` to read current state.
   - Run `agsearch "<job_name>"` to recall full historical context from PostgreSQL `archive_main@arcana.boo`.
   - Read the corresponding project directory (`cwd`) and state files (`state.json` / `project_pending.md`).
   - Immediately report current status and resume execution in Antigravity.

2. **When User asks for task status or list**:
   - Execute `/Users/jrjohn/bin/agjobs` or point the user to [CLAUDE_JOBS.md](file:///Users/jrjohn/.gemini/antigravity/scratch/CLAUDE_JOBS.md).

3. **Background Daemon Maintenance**:
   - Ensure `com.jrjohn.antigravity-archive.plist` remains loaded in launchd.
