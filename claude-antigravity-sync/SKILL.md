---
name: claude-antigravity-sync
description: Synchronizes Claude Code Agent Jobs into Antigravity conversations, PostgreSQL RAG archive, and manages CLI bridge tools (agjobs, agload).
---

# Claude Code & Antigravity Trajectory Sync Skill

This skill provides full, bi-directional knowledge synchronization and automated menu registration for **Claude Code Agent Jobs (`~/.claude/jobs/`)** inside **Antigravity**.

---

## 📦 1-Click Quick Installation

To install this skill and all CLI bridge tools (`agjobs`, `agload`, Python scripts, launchd daemon) on any machine:

```bash
git clone https://github.com/jrjohn/arcana-skills.git
cd arcana-skills/claude-antigravity-sync
./install.sh
```

---

## 🏗️ Architecture Overview

```
[Claude Code Jobs] ~/.claude/jobs/*/state.json
       │
       ├── 1. Transcripts Sync ──► ~/.gemini/antigravity/brain/claude-*/.system_generated/logs/transcript.jsonl
       │
       ├── 2. Native Conversations ──► agentapi new-conversation (Registers in Conversations sidebar)
       │
       └── 3. Vector & RAG Archive ──► PostgreSQL archive_main@arcana.boo (bge-m3 1024-dim embeddings)
```

- **Trajectory Sync Direction**: One-way (`Claude Code -> Antigravity`) to preserve Claude's daemon state locks, avoid schema mismatch, and prevent echo loops.
- **RAG Knowledge Search**: Bi-directional (`Antigravity ↔ Claude Code`) via shared PostgreSQL `archive_main@arcana.boo` using `agsearch` / `osearch`.

---

## 🛠️ Package File Structure

```text
claude-antigravity-sync/
├── SKILL.md                              # Skill definition & agent instructions
├── install.sh                            # 1-Click installer script
├── bin/
│   ├── agjobs                            # CLI tool to list live jobs & conversations
│   └── agload                            # CLI tool to load/resume any job
└── scripts/
    ├── sync_claude_to_antigravity.py     # Converts jobs to brain transcripts
    ├── batch_create_conversations.py     # Uses official agentapi to create native UI items
    ├── claude_jobs_aggregator.py         # Aggregates live jobs & conversations
    ├── ag2archive_pg.py                  # Syncs vector embeddings to PostgreSQL
    ├── sync_all.sh                       # Master sync execution script
    └── com.jrjohn.antigravity-archive.plist # Launchd background daemon config
```

---

## 🤖 Agent Instructions & Rules

1. **When User asks to load or continue a job** (e.g., `"載入 Somnics Cloud 統計"`, `"繼續 MIS"`):
   - Execute `/Users/jrjohn/bin/agload "<job_name>"` to read current state.
   - Run `agsearch "<job_name>"` to recall full historical context from PostgreSQL `archive_main@arcana.boo`.
   - Read the corresponding project directory (`cwd`) and state files (`state.json` / `project_pending.md`).
   - Immediately report current status and resume execution in Antigravity.

2. **When User asks for task status or list**:
   - Execute `/Users/jrjohn/bin/agjobs` or point the user to [CLAUDE_JOBS.md](file:///Users/jrjohn/.gemini/antigravity/scratch/CLAUDE_JOBS.md).

3. **Background Daemon Maintenance**:
   - Ensure `com.jrjohn.antigravity-archive.plist` remains loaded in launchd.
