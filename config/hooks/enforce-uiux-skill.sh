#!/bin/bash
#
# Enforce UI/UX Designer Skill Hook
# Triggered after Write|Edit operations on SDD files
# Reminds to use app-uiux-designer.skill for UI Flow generation
#

# Read hook input from stdin (Claude Code passes JSON via stdin)
INPUT_JSON=$(cat)

# Parse file path from JSON input
FILE_PATH=$(echo "$INPUT_JSON" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

# Only check SDD files
if [[ ! "$FILE_PATH" =~ SDD.*\.md$ ]]; then
    exit 0
fi

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

# Read content and check for screen designs
if grep -qiE '## Screen Designs|## Design Views|SCR-' "$FILE_PATH" 2>/dev/null; then
    echo ""
    echo "========================================"
    echo "[REMINDER] SDD with screen designs detected!"
    echo "----------------------------------------"
    echo "According to IEC 62304 workflow:"
    echo "  1. Use 'app-uiux-designer.skill' to generate UI Flow"
    echo "  2. Generate Design Tokens + Theme CSS"
    echo "  3. Create HTML UI Flow prototype"
    echo "  4. Capture screenshots"
    echo "  5. Update SDD with UI references"
    echo "  6. Update SRS with Screen References"
    echo "========================================"
    echo ""
fi

exit 0
