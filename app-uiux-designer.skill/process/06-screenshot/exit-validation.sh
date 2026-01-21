#!/bin/bash
# ============================================================================
# Exit Validation: 06-screenshot
# ============================================================================
# Purpose: Validate that 06-screenshot phase is complete before proceeding
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
echo -e "${BLUE}  Exit Validation: 06-screenshot${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

ERRORS=0
WARNINGS=0
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')

# Check 1: Screenshot directories exist
echo -e "${BLUE}[1/3] Screenshot Directories${NC}"
if [ -d "screenshots/ipad" ]; then
    echo -e "  ${GREEN}✅${NC} screenshots/ipad/ exists"
else
    echo -e "  ${YELLOW}⚠️${NC} screenshots/ipad/ missing"
    mkdir -p screenshots/ipad
    WARNINGS=$((WARNINGS+1))
fi

if [ -d "screenshots/iphone" ]; then
    echo -e "  ${GREEN}✅${NC} screenshots/iphone/ exists"
else
    echo -e "  ${YELLOW}⚠️${NC} screenshots/iphone/ missing"
    mkdir -p screenshots/iphone
    WARNINGS=$((WARNINGS+1))
fi

# Check 2: Screenshot count
echo ""
echo -e "${BLUE}[2/3] Screenshot Count${NC}"
IPAD_SCREENSHOTS=$(find screenshots/ipad -name "*.png" 2>/dev/null | wc -l | tr -d ' ')
IPHONE_SCREENSHOTS=$(find screenshots/iphone -name "*.png" 2>/dev/null | wc -l | tr -d ' ')

echo -e "  ${BLUE}📸${NC} iPad screenshots: $IPAD_SCREENSHOTS / Expected: $IPAD_COUNT"
echo -e "  ${BLUE}📸${NC} iPhone screenshots: $IPHONE_SCREENSHOTS / Expected: $IPAD_COUNT"

if [ "$IPAD_SCREENSHOTS" -eq 0 ] && [ "$IPHONE_SCREENSHOTS" -eq 0 ]; then
    echo -e "  ${YELLOW}⚠️${NC} No screenshots generated yet"
    echo -e "      Run: node capture-screenshots.js"
    WARNINGS=$((WARNINGS+1))
elif [ "$IPAD_SCREENSHOTS" -lt "$IPAD_COUNT" ]; then
    echo -e "  ${YELLOW}⚠️${NC} Some iPad screenshots missing"
    WARNINGS=$((WARNINGS+1))
else
    echo -e "  ${GREEN}✅${NC} iPad screenshots complete"
fi

# Check 3: Error log (if exists)
echo ""
echo -e "${BLUE}[3/3] Error Log Check${NC}"
if [ -f "workspace/screenshot-error-log.json" ]; then
    FAILURES=$(grep -c '"success": false' workspace/screenshot-error-log.json 2>/dev/null || echo "0")
    if [ "$FAILURES" -gt 0 ]; then
        echo -e "  ${RED}❌${NC} $FAILURES screenshot failures logged"
        echo -e "      Review: workspace/screenshot-error-log.json"
        echo -e "      Action: Return to 03-generation to fix missing screens"
        ERRORS=$((ERRORS+1))
    else
        echo -e "  ${GREEN}✅${NC} No failures in error log"
    fi
else
    echo -e "  ${GREEN}✅${NC} No error log (no failures)"
fi

# Summary
echo ""
echo -e "${BLUE}============================================${NC}"
if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️ 06-screenshot Exit Validation PASSED with warnings${NC}"
        echo -e "   Warnings: $WARNINGS"
    else
        echo -e "${GREEN}✅ 06-screenshot Exit Validation PASSED${NC}"
    fi
    echo ""
    exit 0
else
    echo -e "${RED}❌ 06-screenshot Exit Validation FAILED${NC}"
    echo -e "   Errors: $ERRORS"
    echo ""
    exit 1
fi
