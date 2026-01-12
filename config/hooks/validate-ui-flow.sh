#!/bin/bash
#
# Validate UI Flow Hook
# Triggered after Write|Edit operations on files
# Validates HTML UI Flow files for common issues
#

# Get the file path from environment (set by Claude Code hooks)
FILE_PATH="${CLAUDE_FILE_PATH:-}"

# Only validate UI Flow HTML files
if [[ ! "$FILE_PATH" =~ \.html$ ]] || [[ ! "$FILE_PATH" =~ (ui-flow|uiflow|screen) ]]; then
    exit 0
fi

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

# Validation checks
ERRORS=()

# Check for empty href attributes (navigation issues)
if grep -q 'href=""' "$FILE_PATH" 2>/dev/null; then
    ERRORS+=("Empty href attributes found - navigation links may be broken")
fi

# Check for missing screen IDs
if grep -q 'id=""' "$FILE_PATH" 2>/dev/null; then
    ERRORS+=("Empty id attributes found - screen references may be incomplete")
fi

# Check for TODO markers
if grep -qi 'TODO\|FIXME\|XXX' "$FILE_PATH" 2>/dev/null; then
    ERRORS+=("TODO/FIXME markers found - review before finalizing")
fi

# Check for placeholder images
if grep -q 'src="placeholder\|src="TODO\|src=""' "$FILE_PATH" 2>/dev/null; then
    ERRORS+=("Placeholder or empty image sources found")
fi

# Output validation results
if [ ${#ERRORS[@]} -gt 0 ]; then
    echo "UI Flow Validation Warnings:"
    for error in "${ERRORS[@]}"; do
        echo "  - $error"
    done
    # Don't fail the hook, just warn
    exit 0
fi

exit 0
