# AFP Framework (Anti-Fragile Protocol)

## Overview

AFP provides state persistence and crash recovery for the DevOps skill workflow.

## Principles

1. **State Persistence**: All progress saved to `.devops/` directory
2. **Crash Recovery**: Sessions resume from last completed node
3. **Health Monitoring**: Quick validation of state integrity
4. **Graceful Degradation**: Partial failures don't lose progress

## Workspace Structure

```
{project-root}/.devops/
├── current-process.json  # AFP state file
├── init.json             # Node 00 output
├── infra.json            # Node 01 output
├── pipeline.json         # Node 02 output
├── build.json            # Node 03 output
├── test.json             # Node 04 output
├── deploy.json           # Node 05 output
├── release.json          # Node 06 output
├── monitor.json          # Node 07 output
└── verify.json           # Node 08 output
```

## State Schema

```json
{
  "session_id": "uuid-v4",
  "current_node": "00-init",
  "project_name": "",
  "project_type": [],
  "deploy_targets": [],
  "started_at": "ISO8601",
  "updated_at": "ISO8601",
  "completed_nodes": [],
  "node_outputs": {}
}
```

## Recovery Operations

### Check Current State
```bash
cat .devops/current-process.json | jq .
```

### Resume from Last Node
Read `current_node` from state file and resume execution.

### Reset Session
```bash
rm -rf .devops/
```

## State Transitions

```
[New Session] → [Init State] → [Node Execution] → [Save State] → [Next Node?]
                                      ↑                                |
                                      └────────────── Yes ─────────────┘
                                                       ↓ No
                                                  [Complete]
```
