#!/bin/bash
# ============================================================================
# remove-heading-numbers.sh
# Remove manual numbering from Markdown file headings
#
# Purpose: Ensure MD files don't contain manual numbering for correct auto-numbering during DOCX conversion
#
# Usage:
#   bash remove-heading-numbers.sh <input.md>
#   bash remove-heading-numbers.sh <input.md> <output.md>
#
# Example:
#   bash remove-heading-numbers.sh SRS-Project-1.0.md
#   bash remove-heading-numbers.sh SRS-Project-1.0.md SRS-Project-cleaned.md
#
# Supported numbering formats:
#   ## 1. Introduction       -> ## Introduction
#   ### 1.1 Document Purpose -> ### Document Purpose
#   #### 1.1.1 Overview      -> #### Overview
#   ##### 1.1.1.1 Details    -> ##### Details
# ============================================================================

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check parameters
if [ $# -lt 1 ]; then
    echo -e "${RED}Error: Please provide input file${NC}"
    echo "Usage: $0 <input.md> [output.md]"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${2:-$INPUT_FILE}"

# Check if file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}Error: Cannot find file '$INPUT_FILE'${NC}"
    exit 1
fi

# Create backup
BACKUP_FILE="${INPUT_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$INPUT_FILE" "$BACKUP_FILE"
echo -e "${YELLOW}Created backup: $BACKUP_FILE${NC}"

# Calculate number of manual numberings before removal
BEFORE_COUNT=$(grep -cE '^#{1,6} [0-9]+\.' "$INPUT_FILE" || echo 0)

# Use sed to remove manual numbering
# Supported formats: ## X. / ## X.Y / ## X.Y.Z / ## X.Y.Z.W / ## X.Y.Z.W.V
sed -E '
  s/^(#{1,6}) ([0-9]+\.) /\1 /
  s/^(#{1,6}) ([0-9]+\.[0-9]+) /\1 /
  s/^(#{1,6}) ([0-9]+\.[0-9]+\.[0-9]+) /\1 /
  s/^(#{1,6}) ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) /\1 /
  s/^(#{1,6}) ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) /\1 /
' "$BACKUP_FILE" > "$OUTPUT_FILE"

# Calculate number of manual numberings after removal
AFTER_COUNT=$(grep -cE '^#{1,6} [0-9]+\.' "$OUTPUT_FILE" || echo 0)
REMOVED_COUNT=$((BEFORE_COUNT - AFTER_COUNT))

# Output results
if [ "$REMOVED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Successfully removed $REMOVED_COUNT manual numbering(s)${NC}"
    echo -e "${GREEN}   Output file: $OUTPUT_FILE${NC}"

    # Show some change examples
    echo ""
    echo "Change examples:"
    diff "$BACKUP_FILE" "$OUTPUT_FILE" | grep -E '^[<>].*^#{1,6}' | head -6 || true
else
    echo -e "${YELLOW}ℹ️  No manual numbering found in file${NC}"
fi

# If output file and input file are the same, ask about deleting backup
if [ "$INPUT_FILE" = "$OUTPUT_FILE" ]; then
    echo ""
    echo -e "${YELLOW}Note: Backup file kept at $BACKUP_FILE${NC}"
    echo "To delete backup, execute: rm \"$BACKUP_FILE\""
fi

echo ""
echo "Complete!"
