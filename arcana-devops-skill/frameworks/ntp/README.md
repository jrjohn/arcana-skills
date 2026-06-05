# NTP Framework (Node Transition Protocol)

## Overview

NTP manages gated transitions between COR nodes, ensuring each phase is properly completed before proceeding.

## Principles

1. **Gate Validation**: Every transition requires exit validation
2. **Blocking**: Failed validation blocks progression
3. **Logging**: All transitions are logged in AFP state
4. **Reversibility**: Blocked transitions don't corrupt state

## Transition Flow

```
[Current Node] → [Exit Validation] → PASS → [Update State] → [Next Node]
                                   → FAIL → [Block + Report]
```

## Exit Validation Script

Each node has `exit-validation.sh`:

```bash
#!/bin/bash
set -e
# Check 1: Required outputs exist
# Check 2: Output format is valid
# Check 3: Content meets criteria
# Exit 0 = PASS, Exit 1 = FAIL
```

## Validation Categories

| Category | Description | Example |
|----------|-------------|---------|
| Existence | File/directory exists | `[ -f init.json ]` |
| Format | Correct JSON/YAML format | `jq empty file.json` |
| Content | Required fields present | `jq '.field'` |
| Integrity | Data consistency | Cross-reference checks |
| Runtime | Service health checks | `curl http://localhost:8080/health` |

## Gate Types

### Hard Gate (Blocking)
Must pass to proceed. Failure blocks progression.
Used for: critical security rules (C1-C6), required outputs.

### Soft Gate (Warning)
Warns but allows proceeding.
Used for: recommendations (R1-R4), optional components.

## Blocked Transition Handling

When blocked:
1. Display clear error message
2. Explain what failed and why
3. Provide actionable fix instructions
4. Allow user to re-run validation after fixing
