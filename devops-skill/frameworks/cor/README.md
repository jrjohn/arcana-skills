# COR Framework (Chain of Repository)

## Overview

COR is a sequential node-based workflow pattern for the DevOps skill. Each node represents a distinct phase of the DevOps setup process.

## Principles

1. **Sequential Execution**: Nodes execute in defined order (00 → 08)
2. **Single Responsibility**: Each node has one primary purpose
3. **Clear Boundaries**: Entry and exit conditions are explicit
4. **State Persistence**: Progress is saved after each node

## Node Chain

```
00-init → 01-infra → 02-pipeline → 03-build → 04-test → 05-deploy → 06-release → 07-monitor → 08-verify
```

## Node Structure

```
process/{NN}-{name}/
├── README.md           # Node documentation
└── exit-validation.sh  # Gate validation script
```

## Node Contract

Each node must:
1. Have a README.md documenting purpose, actions, and exit criteria
2. Have an exit-validation.sh that validates completion
3. Save output to `{project-root}/.devops/{name}.json`
4. Update AFP state (`current-process.json`)

## Error Handling

- If a node fails, execution stops at that node
- User is informed of failure point with actionable guidance
- Recovery starts from the failed node (no need to restart)
- Partial state is preserved for investigation

## Best Practices

1. **Naming**: Use descriptive names (e.g., `00-init`)
2. **Documentation**: Each node MUST have README.md
3. **Validation**: Each node MUST have exit-validation.sh
4. **Independence**: Nodes should be re-runnable
5. **Idempotence**: Running a node twice produces the same result
