#!/bin/bash
# ============================================================================
# Exit Validation: 00-init
# ============================================================================
# Purpose: Validate that 00-init phase is complete before proceeding
# Usage: bash exit-validation.sh [project-04-ui-flow-path]
# ============================================================================

set -e
PROJECT_PATH="${1:-.}"
cd "$PROJECT_PATH" 2>/dev/null || { echo "Error: Cannot access $PROJECT_PATH"; exit 1; }

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Exit Validation: 00-init${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

ERRORS=0

# Check 1: Core files exist
echo -e "${BLUE}[1/4] Core Files${NC}"
CORE_FILES=("index.html" "device-preview.html" "shared/project-theme.css" "shared/notify-parent.js")
for file in "${CORE_FILES[@]}"; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file" | tr -d ' ')
        echo -e "  ${GREEN}✅${NC} $file ($lines lines)"
    else
        echo -e "  ${RED}❌${NC} $file missing"
        ERRORS=$((ERRORS+1))
    fi
done

# Check 2: Required scripts exist
echo ""
echo -e "${BLUE}[2/4] Required Scripts${NC}"
SCRIPT_FILES=("capture-screenshots.js" "validate-navigation.js")
for file in "${SCRIPT_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✅${NC} $file"
    else
        echo -e "  ${RED}❌${NC} $file missing"
        ERRORS=$((ERRORS+1))
    fi
done

# Check 3: Template variables replaced
echo ""
echo -e "${BLUE}[3/4] Template Variables${NC}"
UNREPLACED=$(grep -roh '{{[A-Z_]*}}' *.html 2>/dev/null | sort -u | wc -l | tr -d ' ')
if [ "$UNREPLACED" -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} All variables replaced"
else
    echo -e "  ${RED}❌${NC} Found $UNREPLACED unreplaced variables"
    grep -roh '{{[A-Z_]*}}' *.html 2>/dev/null | sort -u | head -5
    ERRORS=$((ERRORS+1))
fi

# Check 4: Workspace initialized
echo ""
echo -e "${BLUE}[4/4] Workspace${NC}"
if [ -f "workspace/current-process.json" ]; then
    echo -e "  ${GREEN}✅${NC} workspace/current-process.json exists"
else
    echo -e "  ${RED}❌${NC} workspace/current-process.json missing"
    ERRORS=$((ERRORS+1))
fi

if [ -d "workspace/context" ] && [ -d "workspace/state" ]; then
    echo -e "  ${GREEN}✅${NC} workspace directories exist"
else
    echo -e "  ${YELLOW}⚠️${NC} workspace subdirectories incomplete"
fi

# Summary
echo ""
echo -e "${BLUE}============================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ 00-init Exit Validation PASSED${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ 00-init Exit Validation FAILED${NC}"
    echo -e "   Errors: $ERRORS"
    echo ""
    exit 1
fi
